import random
from datetime import datetime, timedelta
import pytz

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from genesishealth.apps.readings.models import GlucoseReading

random.seed()


def date_str_to_datetime(date_str):
    year, month, day = map(int, date_str.split("/"))
    return pytz.utc.localize(datetime(year, month, day))


class Command(BaseCommand):
    args = '<username> <start_date> <end_date>'
    help = 'Creates sample readings for a given user and between given dates (format: MM/DD/YYYY)'

    def handle(self, username, start_date, end_date, **options):
        try:
            user = User.objects.get(username=username)
            user.glucose_readings.all().delete()
            start_date = date_str_to_datetime(start_date)
            end_date = date_str_to_datetime(end_date)
            for i in range((end_date - start_date).days + 1):
                d = start_date + timedelta(days=i)
                for i in range(3):
                    reading_datetime_utc = pytz.utc.localize(
                        datetime(d.year, d.month, d.day, random.randint(0, 23), random.randint(0, 59)))
                    glucose_value = random.randint(70, 135)
                    measure_type = random.choice(
                        (GlucoseReading.MEASURE_TYPE_BEFORE, GlucoseReading.MEASURE_TYPE_AFTER, GlucoseReading.MEASURE_TYPE_NORMAL))
                    GlucoseReading.objects.create(patient=user,
                                           glucose_value=glucose_value,
                                           reading_datetime_utc=reading_datetime_utc,
                                           measure_type=measure_type)
        except Exception as e:
            raise CommandError("There was a problem creating your test readings: %s" % e)
