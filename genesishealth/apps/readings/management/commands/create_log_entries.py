"""A command for adding log entries for readings imported into the system."""
from dateutil.parser import parse
from django.core.management.base import BaseCommand

from genesishealth.apps.gdrives.models import GDriveLogEntry
from genesishealth.apps.readings.models import GlucoseReading


class Command(BaseCommand):
    def add_arguments(self, parser) -> None:
        parser.add_argument('start_date', type=str)

    def handle(self, *args, **options):
        start_date = parse(options['start_date'])
        lonely_readings = GlucoseReading.objects.filter(
            gdrive_log_entry__isnull=True, reading_datetime_utc__gt=start_date)
        reading: GlucoseReading
        count = 0
        for reading in lonely_readings:
            entry = GDriveLogEntry.objects.create(
                meid=reading.device.meid if reading.device else None,
                device=reading.device,
                reading_datetime_utc=reading.reading_datetime_utc,
                glucose_value=reading.glucose_value,
                raw_data='',
                successful=True,
                reading=reading
            )
            # Need to update the date_created column
            entry.date_created = reading.reading_datetime_utc
            entry.save()
            count += 1
        print(f"Added log entries for {count} readings.")
