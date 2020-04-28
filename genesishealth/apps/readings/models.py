import json
import logging
import random
import socket

from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.template.loader import render_to_string
from django.utils.timezone import get_default_timezone, now

from genesishealth.apps.alerts.models import PatientAlert
from genesishealth.apps.gdrives.models import GDrive, GDriveLogEntry
from genesishealth.apps.monitoring.models import ReadingServer
from genesishealth.apps.readings.tasks import post_processing
from genesishealth.apps.utils.encrypt import encrypt
from genesishealth.apps.utils.func import utcnow
from genesishealth.external.middleman import parse

import pytz


alert_logger = logging.getLogger('alerts')


class ModelWithNotes(models.Model):
    class Meta:
        abstract = True

    def get_note_for_user(self, user):
        cls = self.notes.model
        try:
            return self.notes.get(author=user)
        except cls.DoesNotExist:
            return ''

    def set_note_for_user(self, user, content):
        cls = self.notes.model
        note, created = cls.objects.get_or_create(author=user, entry=self)
        note.content = content
        note.save()


class GlucoseReading(ModelWithNotes):
    MEASURE_TYPE_NORMAL = 'normal'
    MEASURE_TYPE_BEFORE = 'before_meal'
    MEASURE_TYPE_AFTER = 'after_meal'
    MEASURE_TYPE_TEST = 'test_mode'
    MEASURE_TYPES = (
        (MEASURE_TYPE_NORMAL, 'Normal'),
        (MEASURE_TYPE_BEFORE, 'Before meal'),
        (MEASURE_TYPE_AFTER, 'After meal'),
        (MEASURE_TYPE_TEST, 'TEST mode')
    )

    PUBLIC_MEASURE_TYPES = (
        (MEASURE_TYPE_NORMAL, 'Normal'),
        (MEASURE_TYPE_BEFORE, 'Before meal'),
        (MEASURE_TYPE_AFTER, 'After meal')
    )

    patient = models.ForeignKey(User, models.SET_NULL,
                                related_name='glucose_readings', null=True)
    device = models.ForeignKey(
        GDrive, models.SET_NULL, related_name='readings', null=True)
    measure_type = models.CharField(
        choices=MEASURE_TYPES,
        max_length=100,
        default=MEASURE_TYPE_NORMAL)
    reading_datetime_utc = models.DateTimeField()
    reading_datetime_offset = models.IntegerField(default=0)
    glucose_value = models.IntegerField()
    committed = models.BooleanField(default=False)
    in_use = models.BooleanField(default=False)
    commit_attempts = models.IntegerField(default=0)
    permanently_failed = models.BooleanField(default=False)
    unique_id = models.CharField(max_length=255, blank=True)
    alert_sent = models.BooleanField(default=False)
    test_reading = models.BooleanField(default=False)
    manually_changed_time = models.DateTimeField(null=True)
    manually_changed_by = models.ForeignKey(
        User, models.SET_NULL, related_name="+", null=True)
    raw_data = models.TextField()
    offset_adjusted = models.BooleanField(default=False)

    @classmethod
    def adjust_faulty_offset_datetime(cls, dt, timezone):
        return timezone.localize(datetime(
            year=dt.year, month=dt.month, day=dt.day, hour=dt.hour,
            minute=dt.minute, second=dt.second, microsecond=dt.microsecond
        )).astimezone(pytz.UTC)

    @classmethod
    def generate_push_request(cls):
        """Returns a tuple, containing what should be the first two arguments
        to outgoingAPIRequest.create.
        Returns False if there are no readings to push."""
        from genesishealth.apps.accounts.models import PatientProfile
        data = {
            'source_name': settings.API_SOURCE_NAME,
            'secret_key': settings.API_SECRET_KEY}
        batch_data = {'batch': []}
        # Now generate the large batch of data

        patient_ids = cls.objects.filter(
            patient__patient_profile__is_verizon_patient=True,
            committed=False
        ).order_by('patient').distinct('patient').values('patient__pk')
        patients = PatientProfile.verizon_patients.get_users().filter(
            pk__in=patient_ids)
        if patients.count() == 0:
            return False
        reading_ids = set([])

        for patient in patients:
            readings = patient.glucose_readings.filter(
                committed=False,
                commit_attempts__lte=settings.MAX_API_ATTEMPTS)
            if not readings:
                continue

            info = {
                'user': patient.patient_profile.api_username,
                'user_instance_id': patient.get_profile().verizon_instance_id,
                'measurements': []}

            # Generate measurements.
            for m in readings:
                reading_ids.update([m.id])
                m.commit_attempts += 1
                m.save()

                time_format = '%Y-%m-%dT%H:%M:%S'
                reading_time = m.reading_datetime.strftime(time_format)
                utc_time = m.reading_datetime_utc.strftime(time_format)
                reading_data = {
                    'unique_id': str(m.id),
                    'unit': settings.API_UNIT,
                    'source_id': m.device and m.device.device_id or 'N/A',
                    'value': str(m.glucose_value),
                    'reading_datetime': reading_time,
                    'reading_datetime_utc': utc_time,
                    'type': settings.API_OBSERVATION_TYPE
                }

                info['measurements'].append(reading_data)

            batch_data['batch'].append(info)

        data['data'] = json.dumps(batch_data)
        return (data, {'reading_ids': list(reading_ids)})

    @classmethod
    def generate_raw_reading(cls, patient, **kwargs):
        """Generates an encrypted, raw reading that can be sent to the reading
        server."""
        device = patient.patient_profile.get_device()
        if not device:
            raise Exception(
                'generate_raw_reading will not work for a patient without a'
                ' device.')
        # Create random / default data if user has not specified.
        glucose_value = kwargs.get('glucose_value', random.randint(40, 160))
        measure_type = kwargs.get('measure_type', random.randint(0, 2))
        reading_datetime = kwargs.get(
            'reading_datetime',
            utcnow()).astimezone(patient.patient_profile.timezone)
        if 'offset' in kwargs:
            offset = kwargs['offset']
        else:
            # Figure out offset from timezone.
            offset = reading_datetime.strftime('%z')[:-2]
        # It will give it to us as +0100 (e.g.). trim off last two digits.
        hour = "%s,%s" % (reading_datetime.hour, offset)

        c = {
            'gateway_type': '4123',
            'gateway_id': '0000000000000001',
            'device_type': '4123',
            'serial_number': device.device_id,
            'meid': device.meid,
            'extension_id': '1',
            'year': reading_datetime.year,
            'month': reading_datetime.month,
            'day': reading_datetime.day,
            'hour': hour,
            'minute': reading_datetime.minute,
            'second': reading_datetime.second,
            'data_type': '1',
            'value_1': glucose_value,
            'value_2': '0',
            'value_3': '0',
            'value_4': measure_type,
            'value_5': '0',
            'value_6': '0'
        }
        return cls.raw_reading_from_dict(c), c

    @classmethod
    def generate_raw_reading_for_device(cls, device, **kwargs):
        """Generates an encrypted, raw reading that can be sent to the reading
        server."""
        # Create random / default data if user has not specified.
        glucose_value = kwargs.get('glucose_value', random.randint(40, 160))
        measure_type = kwargs.get('measure_type', random.randint(0, 2))
        if device.patient:
            tz = device.patient.patient_profile.timezone
        else:
            tz = get_default_timezone()
        reading_datetime = kwargs.get(
            'reading_datetime', utcnow()).astimezone(tz)
        if 'offset' in kwargs:
            offset = kwargs['offset']
        else:
            # Figure out offset from timezone.
            offset = reading_datetime.strftime('%z')[:-2]
        # It will give it to us as +0100 (e.g.). trim off last two digits.
        hour = "%s,%s" % (reading_datetime.hour, offset)

        c = {
            'gateway_type': '4123',
            'gateway_id': '0000000000000001',
            'device_type': '4123',
            'serial_number': device.device_id,
            'meid': device.meid,
            'extension_id': '1',
            'year': reading_datetime.year,
            'month': reading_datetime.month,
            'day': reading_datetime.day,
            'hour': hour,
            'minute': reading_datetime.minute,
            'second': reading_datetime.second,
            'data_type': '1',
            'value_1': glucose_value,
            'value_2': '0',
            'value_3': '0',
            'value_4': measure_type,
            'value_5': '0',
            'value_6': '0'
        }
        return cls.raw_reading_from_dict(c), c

    @classmethod
    def raw_reading_from_dict(cls, data):
        """Takes a dict of values and generates a reading from it."""
        # Encrypt all the data.
        encrypted_data = {}
        for key, value in data.items():
            encrypted_value = encrypt(value)
            # The data has to be spaced out into bytes (two characters)
            r = range(0, len(encrypted_value), 2)
            bytes = [encrypted_value[i:i + 2] for i in r]
            encrypted_data[key] = ' '.join(bytes)
        # Render reading data
        return render_to_string('readings/raw_reading', encrypted_data)

    @classmethod
    def send_raw_reading(cls, reading, reading_server=None):
        # Connect to server
        if reading_server is None:
            reading_server = random.choice(settings.READING_SERVER_LOCATIONS)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(40)
        try:
            sock.connect((reading_server, settings.GDRIVE_READING_PORT))
        except socket.error:
            pass
        sock.send(reading)
        response = sock.recv(7)
        sock.close()
        return response

    @classmethod
    def parse_measure_type(cls, measure_type_number):
        measure_types = [mt[0] for mt in GlucoseReading.MEASURE_TYPES]
        try:
            return measure_types[measure_type_number]
        except IndexError:
            pass

    @classmethod
    def process_reading(cls, data, server_name=None, log_results=True):
        """Parses a decrypted reading and saves a reading.
        Returns a three-tuple: (success(True/False), decrypted data, error
        (if applicable)."""
        def log(status, **kwargs):
            if log_results:
                try:
                    reading_server = ReadingServer.objects.get(
                        log_alias=server_name)
                except ReadingServer.DoesNotExist:
                    reading_server = None
                kwargs.setdefault('reading_server', reading_server)
                GDriveLogEntry.objects.create(status=status, **kwargs)

        def justplain(d):
            d2 = dict()
            for k, v in d.items():
                d2[k.lower()] = v['plain']
            return d2

        def parse_date_time(year, month, day, hour=0, minute=0, second=0):
            return datetime(
                int(year), int(month), int(day),
                int(hour), int(minute), int(second))

        # Decrypt data.
        reading_data = {}
        decrypted = parse.parse_and_decrypt(
            data, settings.GDRIVE_DECRYPTION_KEY)
        # Update decrypted data to plain text.
        clean = justplain(decrypted)
        # Pull out data.
        raw_data = str(clean)
        # Hour and timezone are separated
        hour, offset = map(int, clean['hour'].split(','))
        # Calculate local time of reading
        reading_datetime = parse_date_time(
            clean['year'], clean['month'], clean['day'],
            hour, clean['minute'], clean['second'])

        # Unapply offset to get utc time
        reading_data['reading_datetime_utc'] = pytz.utc.normalize(
            pytz.utc.localize(reading_datetime - timedelta(hours=offset))
        )
        reading_data['reading_datetime_offset'] = offset

        # Value of the reading is value1.
        reading_data['glucose_value'] = int(clean['value1'])

        # Determine measure type
        reading_data['measure_type'] = cls.parse_measure_type(
            int(clean['value4']))

        # Get patient and device
        meid = clean.get('meid')
        reading_data.update({
            'patient': None,
            'device': None,
        })
        if meid:
            try:
                reading_data['device'] = GDrive.objects.get(meid__iexact=meid)
            except GDrive.DoesNotExist:
                pass
        if reading_data['device']:
            reading_data['patient'] = reading_data['device'].patient

        log_kwargs = {
            'meid': meid,
            'device': reading_data['device'],
            'reading_datetime_utc': reading_data['reading_datetime_utc'],
            'glucose_value': reading_data['glucose_value'],
            'raw_data': raw_data,
            'successful': False
        }

        try:
            # Make sure device is valid.
            assert reading_data['device'] is not None, 'Invalid device.'
        except AssertionError as e:
            msg = 'Reading processing failed with error: %s' % e
            log(msg, **log_kwargs)
            return (False, clean, msg, None, None)

        try:
            # Make sure reading is unique.
            assert GlucoseReading.objects.filter(
                raw_data=raw_data).count() == 0, 'Duplicate reading.'
            # Validate measure_type
            assert reading_data['measure_type'] is not None, 'Invalid measure type.' # noqa
        except AssertionError as e:
            msg = 'Reading processing failed with error: %s' % e
            log(msg, **log_kwargs)
            return (False, clean, msg, None, None)

        # Adding raw_data now, because previously we couldn't use it
        # for filtering
        reading_data['raw_data'] = raw_data
        patient = reading_data['patient']
        if patient:
            if (reading_data['reading_datetime_offset'] == 0 and
                    patient.patient_profile.timezone):
                reading_data['reading_datetime_utc'] = cls\
                    .adjust_faulty_offset_datetime(
                        reading_data['reading_datetime_utc'],
                        patient.patient_profile.timezone
                )
                log_kwargs['reading_datetime_utc'] = reading_data[
                    'reading_datetime_utc']
                reading_data['offset_adjusted'] = True
        # Save the reading.
        try:
            reading = GlucoseReading.objects.create(**reading_data)
        except Exception as e:
            msg = 'Reading creation failed with error: %s' % e
            log(msg, **log_kwargs)
            return (False, clean, msg, None, None)
        # Log the success.
        reading.trigger_alerts()
        log_kwargs['successful'] = True
        log_kwargs['reading'] = reading
        log('Success', **log_kwargs)
        post_processing.delay(reading.pk)
        return (True, clean, '', reading, reading_data['device'].patient)

    def __unicode__(self):
        from genesishealth.apps.accounts.models import PatientProfile
        try:
            return u"%s's reading [%s]" % (
                self.patient.get_full_name(), self.reading_datetime)
        except PatientProfile.DoesNotExist:
            return 'Unassociated reading %s' % self.pk

    def adjust_for_faulty_offset(self):
        if (self.reading_datetime_offset == 0 and
                not self.offset_adjusted and
                self.patient.patient_profile.timezone is not None):
            self.reading_datetime_utc = self.adjust_faulty_offset_datetime(
                self.reading_datetime_utc,
                self.patient.patient_profile.timezone)
            self.offset_adjusted = True
            self.save()

    def generate_csv_row(self):
        """Generates a row for CSV export."""
        if self.device:
            meid = self.device.meid
        else:
            meid = "N/A"

        return [
            self.patient.pk,
            meid,
            self.reading_datetime_utc,
            self.reading_datetime_offset,
            self.measure_type,
            self.glucose_value
        ]

    def is_above_range(self):
        hi = self.patient.healthinformation
        if self.measure_type == GlucoseReading.MEASURE_TYPE_BEFORE:
            maximum = hi.premeal_glucose_goal_maximum
        elif self.measure_type == GlucoseReading.MEASURE_TYPE_AFTER:
            maximum = hi.postmeal_glucose_goal_maximum
        else:
            maximum = hi.postmeal_glucose_goal_maximum

        return self.glucose_value > maximum

    def is_below_range(self):
        hi = self.patient.healthinformation
        if self.measure_type == GlucoseReading.MEASURE_TYPE_BEFORE:
            minimum = hi.premeal_glucose_goal_minimum
        elif self.measure_type == GlucoseReading.MEASURE_TYPE_AFTER:
            minimum = hi.postmeal_glucose_goal_minimum
        else:
            minimum = hi.premeal_glucose_goal_minimum

        return self.glucose_value < minimum

    def is_in_danger_range(self):
        hi = self.patient.healthinformation
        return (self.glucose_value < hi.safe_zone_minimum or
                self.glucose_value > hi.safe_zone_maximum)

    def is_in_range(self):
        hi = self.patient.healthinformation
        if self.measure_type == GlucoseReading.MEASURE_TYPE_BEFORE:
            minimum = hi.premeal_glucose_goal_minimum
            maximum = hi.premeal_glucose_goal_maximum
        elif self.measure_type == GlucoseReading.MEASURE_TYPE_AFTER:
            minimum = hi.postmeal_glucose_goal_minimum
            maximum = hi.postmeal_glucose_goal_maximum
        else:
            minimum = hi.premeal_glucose_goal_minimum
            maximum = hi.postmeal_glucose_goal_maximum
        return self.glucose_value >= minimum and self.glucose_value <= maximum

    def readable_measure_type(self):
        try:
            return dict(GlucoseReading.MEASURE_TYPES)[self.measure_type]
        except KeyError:
            measure_type = "Unknown Measure Type"
            alert_logger.warning(measure_type)
            return measure_type

    def get_glucose_value_display(self):
        if self.glucose_value > settings.GLUCOSE_HI_VALUE:
            return 'HI'
        if self.glucose_value < settings.GLUCOSE_LO_VALUE:
            return 'LO'
        return self.glucose_value

    def mark_change(self, user):
        self.manually_changed_time = now()
        self.manually_changed_by = user
        self.save()

    def trigger_alerts(self):
        if self.patient:
            alerts = self.patient.my_patientalerts.filter(
                active=True, type=PatientAlert.READING_RECEIVED)
            alert_logger.info('Trigger alerts: %s' % repr(alerts))
            for a in alerts:
                a.trigger(
                    time=self.reading_datetime.strftime('%m/%d/%Y %I:%M %p'),
                    value=self.glucose_value)
            self.alert_sent = True
            self.save()

    @property
    def reading_datetime(self):
        """Returns local time."""
        if self.patient is None:
            timezone = get_default_timezone()
        else:
            timezone = self.patient.patient_profile.timezone

        normalized = self.reading_datetime_utc.replace(tzinfo=pytz.utc)
        return normalized.astimezone(timezone)


class GlucoseReadingNote(models.Model):
    """Note on a glucose meter."""
    class Meta:
        unique_together = ('author', 'entry')

    content = models.TextField(blank=True, default="")
    author = models.ForeignKey(User, editable=False, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True, editable=False)
    visible_to_patient = models.BooleanField(default=True, editable=False)
    entry = models.ForeignKey(
        GlucoseReading, editable=False, related_name='notes', on_delete=models.CASCADE)
