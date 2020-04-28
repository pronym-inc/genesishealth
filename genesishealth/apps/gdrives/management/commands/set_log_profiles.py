from dateutil.parser import parse

from django.core.management.base import BaseCommand

from genesishealth.apps.gdrives.models import GDriveTransmissionLogEntry


class Command(BaseCommand):
    def handle(self, from_date_str, **options):
        date = parse(from_date_str)
        targets = GDriveTransmissionLogEntry.objects.filter(
            associated_patient_profile__isnull=True,
            processing_succeeded=True,
            datetime__gte=date)
        print("Updating {} records...".format(targets.count()))
        results = map(lambda x: x.determine_info(), targets)
        print("Updated {} log records".format(results.count(True)))
