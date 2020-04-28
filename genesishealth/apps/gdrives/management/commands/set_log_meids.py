from django.core.management.base import BaseCommand

from genesishealth.apps.gdrives.models import GDriveTransmissionLogEntry


class Command(BaseCommand):
    def handle_noargs(self, **options):
        results = list(map(
            lambda x: x.determine_meid(),
            GDriveTransmissionLogEntry.objects.filter(meid__isnull=True)
        ))
        print("Updated {} log records".format(results.count(True)))
