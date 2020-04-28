"""Readings that were recovered through the system do not have their
proper log entries set.  This script resolves that."""
from datetime import datetime
from django.core.management.base import BaseCommand

from genesishealth.apps.gdrives.models import GDriveTransmissionLogEntry


class Command(BaseCommand):
    def handle(self, **options):
        for log_entry in GDriveTransmissionLogEntry.objects\
                .filter(datetime__gt=datetime(2014, 1, 1))\
                .filter(glucose_value__isnull=True)\
                .filter(reading__isnull=False):
            log_entry.glucose_value = log_entry.reading.glucose_value
            log_entry.save()
