from datetime import time, timedelta, datetime, date

from django.template.loader import render_to_string
from django.db.models import Avg, StdDev
from django.conf import settings

from genesishealth.apps.readings.models import GlucoseReading

def get_datetime(obj):
    """Gets the datetime, using get_datetime_field, of the object."""
    dtf = get_datetime_field(obj)
    return getattr(obj, dtf)

def get_datetime_field(obj):
    """Gets the datetime field of the given object."""
    possibilities = ('reading_datetime_utc', 'reading_datetime', 'datetime')
    for p in possibilities:
        if hasattr(obj, p): return p
    raise Exception('%s has no known datetime field!' % obj)

def get_datetime_field_from_model(model):
    """Helper function because some of the models have different field names for datetime.
    Unlike above, this looks at the model, not at an instance."""
    possibilities = ('reading_datetime_utc', 'reading_datetime', 'datetime')
    field_names = map(lambda x: x.name, model._meta.fields)
    for p in possibilities:
        if p in field_names: return p


class LogbookDay:
    """Not a model.  Represents a single day in the logbook.  Provides all the functionality
    for organizing the days into the logbook format."""
    PERIOD_TYPES = ('monthly', 'daily_four_periods', 'daily_eight_periods')

    PERIOD_DEFINITIONS = {
        'daily_four_periods': [
            {'name': 'Breakfast', 'start_time': timedelta(hours=0)},
            {'name': 'Lunch', 'start_time': timedelta(hours=11)},
            {'name': 'Dinner', 'start_time': timedelta(hours=14)},
            {'name': 'Night', 'start_time': timedelta(hours=22)}
        ],
        'daily_eight_periods': [
            {'name': 'Overnight', 'start_time': timedelta(hours=0)},
            {'name': 'Early Morning', 'start_time': timedelta(hours=6)},
            {'name': 'Late Morning', 'start_time': timedelta(hours=9)},
            {'name': 'Early Afternoon', 'start_time': timedelta(hours=11)},
            {'name': 'Late Afternoon', 'start_time': timedelta(hours=14)},
            {'name': 'Early Evening', 'start_time': timedelta(hours=17)},
            {'name': 'Late Evening', 'start_time': timedelta(hours=19)},
            {'name': 'Bedtime', 'start_time': timedelta(hours=22)}
        ]
    }

    DISPLAY_TYPES_TO_PERIOD_TYPES = {
        'logbook8': 'daily_eight_periods',
        'logbook4': 'daily_four_periods'
    }

    ENTRY_TYPES = ('glucose_readings',)

    @classmethod
    def calculate_stats(cls, days, patient):
        """This class method receives a list of LogbookDays and then parses various stats from them.
        It returns a dictionary with 4 keys - glucose_average, percent_in_target, standard_deviation,
        and number_of_readings - and a list (with size = number of periods) of the values for each
        period."""
        stats = {'glucose_average': [], 'percent_in_target': [], 'standard_deviation': [],
            'number_of_readings': []}

        # Figure out period type by checking first day
        period_type = days[0].period_type

        period_defs = cls.PERIOD_DEFINITIONS[period_type]

        count = 0
        for period in period_defs:
            # Get all the readings into a query set so we can do some analysis.
            reading_ids = []
            for day in days:
                for entry in day.periods[count].entries:
                    if isinstance(entry, GlucoseReading):
                        reading_ids.append(entry.id)
            readings = GlucoseReading.objects.filter(id__in=reading_ids)

            aggregates = readings.aggregate(Avg('glucose_value'), StdDev('glucose_value'))
            readings_in_range = readings.filter(
                glucose_value__range=(patient.healthinformation.premeal_glucose_goal_minimum,
                    patient.healthinformation.postmeal_glucose_goal_maximum))

            if readings.count() == 0: # No div by 0!
                percent_in_target = 0
            else:
                percent_in_target = float(readings_in_range.count()) / readings.count() * 100

            stats['glucose_average'].append(aggregates['glucose_value__avg'])
            stats['percent_in_target'].append(percent_in_target)
            stats['standard_deviation'].append(aggregates['glucose_value__stddev'])
            stats['number_of_readings'].append(readings.count())

            count += 1

        return stats        

    @classmethod
    def generate_logbook_days(cls, patient, start_date, end_date, display_type, cap_entries=settings.MAX_LOGBOOK_ENTRIES):
        """Generates all of the logbook days and fills them with the patient's data.
        cap_entries=<digit> will cap the number of entries per period at <digit>"""
        out_type = cls.DISPLAY_TYPES_TO_PERIOD_TYPES[display_type]
        days = []
        for i in range((end_date - start_date).days + 1):
            days.append(cls(patient, end_date - timedelta(days=i), out_type, cap_entries))
        return days

    @classmethod
    def get_period_info(cls, period_type, timezone):
        """This gets the name, start time, and end time (calculated) for all of the periods in
        the provided period_type, in a list for the given period type.

        The output is a list of dictionaries with period name ("Lunch") and label ("11 AM -
        2 AM")."""
        defs = cls.PERIOD_DEFINITIONS[period_type]
        period_info = []
        count = 0
        start_of_day = datetime.combine(date.today(), time()).replace(tzinfo=timezone)
        for period_def in defs:
            info = {'name': period_def['name']}
            start_datetime = start_of_day + period_def['start_time']
            info['start_time'] = start_datetime.time()
            if len(defs) == (count + 1):
                end_datetime = start_of_day + defs[0]['start_time'] + timedelta(days=1)
            else:
                end_datetime = start_of_day + defs[count + 1]['start_time']
            info['end_time'] = end_datetime.time()
            period_info.append(info)
            count += 1
        return period_info

    def __init__(self, patient, day, period_type, cap_entries=None):
        self.patient = patient
        self.timezone = self.patient.patient_profile.timezone
        # Convert date to datetime for comparison later.
        if isinstance(day, date):
            self.day = self.timezone.localize(datetime.combine(day, time()))
        else:
            self.day = day

        self.weekend = self.day.weekday() in (5, 6)
        self.period_type = period_type
        self.day_start = min([i['start_time'].seconds / 3600 for i in LogbookDay.PERIOD_DEFINITIONS[period_type]])
        self.periods = [LogbookPeriod(self.day, self.period_type, i['name'])\
                         for i in LogbookDay.PERIOD_DEFINITIONS[self.period_type]]

        start_date = self.day + timedelta(hours=self.day_start)
        end_date = start_date + timedelta(days=1) - timedelta(microseconds=1)
        
        for i in LogbookDay.ENTRY_TYPES:
            obj_manager = getattr(self.patient, i)
            datetime_field = get_datetime_field_from_model(obj_manager.model)
            # Figure out what the start of each day is ... e.g. some are 12AM - 12AM, others are 5AM-5AM
            # Query must be adjusted accordingly.
            kwargs = {'%s__range' % datetime_field: (start_date, end_date)}
            items = obj_manager.filter(**kwargs)
            for r in items:
                self.add_entry(r, cap_entries)

        self.sort()

    def __str__(self) -> str:
        return '%s logbook day for %s' % (self.day, self.patient)

    def add_entry(self, entry, cap_entries=None): 
        """Adds a reading (or whatever)."""
        dt = get_datetime(entry)

        for period in self.periods:
            if cap_entries and len(period.entries) >= cap_entries: continue
            if dt >= period.start_time and dt <= period.end_time:
                period.add_entry(entry)
                break

    def sort(self):
        for p in self.periods: p.sort()

class LogbookPeriod:
    """A subdivision of a day.  Not a model - no database records!  Just helps with logbook."""

    ICONS = {
        'BloodPressureReading': 'bp-ico',
        'WeightReading': 'weight-ico',
        'Meal': 'food-ico',
        'ExerciseEvent': 'ex-ico',
        'MedicationEvent': 'meds-ico'
    }

    FORMATS = {
        'GlucoseReading': (('get_glucose_value_display',), '%s <img src="/static/images/mgdl.png" />'),
        'BloodPressureReading': (('systolic_value', 'diastolic_value'), '%s/%s'),
        'WeightReading': (('value',), '%s lbs'),
        'Meal': (('get_carbohydrates',), '%s crb'),
        'ExerciseEvent': (('duration',), '%s'),
        'MedicationEvent': (('dosage', 'units'), '%.1f %s')
    }

    def __init__(self, day, period_type, name):
        self.day = day
        self.period_type = period_type
        self.name = name
        self.entries = []
        self.start_time = self.get_start_time()
        self.end_time = self.get_end_time()

    def add_entry(self, entry):
        self.entries.append(entry)

    def get_definition(self):
        for info in LogbookDay.PERIOD_DEFINITIONS[self.period_type]:
            if info['name'] == self.name:
                return info
        raise Exception('Unknown period_type')

    def get_next_definition(self):
        for index, info in enumerate(LogbookDay.PERIOD_DEFINITIONS[self.period_type]):
            if info['name'] == self.name:
                index = (index + 1) % len(LogbookDay.PERIOD_DEFINITIONS[self.period_type])
                return LogbookDay.PERIOD_DEFINITIONS[self.period_type][index]
        raise Exception('Unknown period_type')

    def get_end_time(self):
        my_info = self.get_next_definition()

        offset = 1 if my_info['start_time'] < self.get_definition()['start_time'] else 0

        return self.day + my_info['start_time'] - timedelta(microseconds=1) + timedelta(days=offset)

    def get_start_time(self):
        my_info = self.get_definition()

        return self.day + my_info['start_time']

    def render_as_html(self, template='reports/logbook/period.html'):
        """Renders to the provided HTML template."""
        entry_list = []
        for entry in self.entries:
            class_name = entry.__class__.__name__
            extra = None
            if class_name == 'GlucoseReading':
                if entry.measure_type == GlucoseReading.MEASURE_TYPE_BEFORE:
                    icon = 'r-apple'
                elif entry.measure_type == GlucoseReading.MEASURE_TYPE_AFTER:
                    icon = 'after-ico'
                else:
                    icon = 'normal-read'

                if entry.is_in_range():
                    extra = 'target-ico'
                elif entry.is_in_danger_range():
                    extra = 'o-exclam'
                elif entry.is_above_range():
                    extra = 'o-up-ico'
                elif entry.is_below_range():
                    extra = 'o-down-ico'
            else:
                icon = LogbookPeriod.ICONS[class_name]
            description_format = LogbookPeriod.FORMATS[class_name]
            attrs = [getattr(entry, i) for i in description_format[0]]
            attrs = tuple(map(lambda x: not callable(x) and x or x(), attrs))
            description = description_format[1] % attrs
            entry_list.append({'icon': icon, 'description': description, 'extra': extra, 'entry': entry,
                'type': class_name.lower()})
        c = {'entries': entry_list, 'start_time': self.start_time, 'end_time': self.end_time}
        
        # strip off new lines.
        return render_to_string(template, c).replace('\n', '')

    def sort(self):
        """Sort entries by datetime."""
        def sort_key(entry):
            dtf = get_datetime_field(entry)
            return getattr(entry, dtf)

        self.entries.sort(key=sort_key)
