"""A command for adding log entries for readings imported into the system."""
from datetime import datetime, timedelta
from typing import Optional

from django.core.management.base import BaseCommand

from genesishealth.apps.readings.models import GlucoseReading


class Command(BaseCommand):
    def add_arguments(self, parser) -> None:
        parser.add_argument('--dry-run', dest='dry-run', action='store_true')

    def handle(self, *args, **options):
        is_dry_run = options['dry-run']
        last_reading_datetime: Optional[datetime] = None
        reading: GlucoseReading
        for reading in GlucoseReading.objects.order_by('id'):
            fixed_datetime = None
            if last_reading_datetime is not None:
                diff = abs((reading.reading_datetime_utc - last_reading_datetime).total_seconds())
                if diff > 1000:
                    fixed_datetime = last_reading_datetime + timedelta(seconds=2)
                    if is_dry_run:
                        print(f"Changing reading {reading} from {reading.reading_datetime_utc} to {fixed_datetime}")
                    else:
                        reading.reading_datetime_utc = fixed_datetime
                        reading.save()
            if fixed_datetime is None:
                last_reading_datetime = reading.reading_datetime_utc
            else:
                last_reading_datetime = fixed_datetime
