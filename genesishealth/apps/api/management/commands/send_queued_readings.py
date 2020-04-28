from django.core.management.base import BaseCommand

from genesishealth.apps.api.models import APIPartner


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for partner in APIPartner.objects.filter(forward_readings=True):
            partner.send_queued_attempts()
