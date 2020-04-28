"""Readings that were recovered through the system do not have their
proper log entries set.  This script resolves that."""
import pytz

from datetime import timedelta, datetime
from django.core.management.base import BaseCommand

from genesishealth.apps.gdrives.models import GDriveTransmissionLogEntry, GDriveLogEntry
from genesishealth.apps.readings.models import GlucoseReading


class Command(BaseCommand):
    def handle(self, **options):
        for log_entry in GDriveTransmissionLogEntry.objects\
                .filter(reading__isnull=True)\
                .filter(datetime__gt=datetime(2014, 1, 1))\
                .filter(resolution='no_patient', recovered=True):
            hour, offset = map(int, log_entry._get_value('hour').split(','))
            dt_args = map(
                int,
                [
                    log_entry._get_value('year'),
                    log_entry._get_value('month'),
                    log_entry._get_value('day'),
                    hour,
                    log_entry._get_value('minute'),
                    log_entry._get_value('second')
                ]
            )
            dt = pytz.UTC.localize(datetime(*dt_args) - timedelta(hours=offset))
            # Now look for our reading.
            try:
                reading = GlucoseReading.objects.get(
                    device__meid=log_entry._get_value('meid'),
                    glucose_value=log_entry._get_value('value1'),
                    reading_datetime_utc=dt
                )
            except GlucoseReading.DoesNotExist:
                print("Could not find glucose reading for {}".format(log_entry.pk))
            except GlucoseReading.MultipleObjectsReturned:
                print("Multiple objects found for {}".format(log_entry.pk))
            else:
                log_entry.reading = reading
                log_entry.save()
                # Now fix the gdrive log entry, if needed.
                try:
                    reading.gdrive_log_entry
                except GDriveLogEntry.DoesNotExist:
                    try:
                        gdrive_log_entry = GDriveLogEntry.objects.get(
                            reading__isnull=True,
                            meid=reading.device.meid,
                            glucose_value=reading.glucose_value,
                            reading_datetime_utc=reading.reading_datetime_utc
                        )
                    except GDriveLogEntry.DoesNotExist:
                        continue
                    except GDriveLogEntry.MultipleObjectsReturned:
                        print("Got multiple objects for {}".format(reading.pk))
                        gdrive_log_entry = GDriveLogEntry.objects.filter(
                            reading__isnull=True,
                            meid=reading.device.meid,
                            glucose_value=reading.glucose_value,
                            reading_datetime_utc=reading.reading_datetime_utc
                        )[0]
                    gdrive_log_entry.reading = reading
                    gdrive_log_entry.save()
