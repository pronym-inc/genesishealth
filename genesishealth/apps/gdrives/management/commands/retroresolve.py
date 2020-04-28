from dateutil.parser import parse

from django.core.management.base import BaseCommand
from django.db.models import Q

from genesishealth.apps.gdrives.models import GDriveTransmissionLogEntry


class Command(BaseCommand):
    def handle(self, from_date_str, **options):
        from_date = parse(from_date_str)
        results = map(
            lambda x: x.retro_resolve(),
            GDriveTransmissionLogEntry.objects.filter(datetime__gte=from_date).
            filter(Q(resolution__isnull=True) |
                   Q(resolution=GDriveTransmissionLogEntry.RESOLUTION_UNRESOLVED))
        )
        print("Updated {} log records".format(len(results)))
