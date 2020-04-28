from django.core.management.base import BaseCommand
from django.utils.timezone import now

from genesishealth.apps.api.models import APIPartner


class Command(BaseCommand):
    def handle(self, *args, **options):
        partners = APIPartner.objects.filter(
            flatfile_connection__isnull=False,
            flatfile_connection__active=True)
        for partner in partners:
            partner.send_wellness_document(now().date())
