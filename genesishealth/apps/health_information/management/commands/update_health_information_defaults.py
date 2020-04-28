from datetime import date

from django.core.management.base import BaseCommand
from django.utils.timezone import now

from genesishealth.apps.health_information.models import (
    HealthProfessionalTargets, HealthInformation)


class Command(BaseCommand):
    help = 'Updates the defaults for health information for all patients.  Do not run this.'

    def handle(self, **options):
        # Should only be run once, hence restricted by date.
        assert now().date() == date(2015, 7, 24)

        def update(obj):
            obj.premeal_glucose_goal_minimum = 70
            obj.premeal_glucose_goal_maximum = 130
            obj.postmeal_glucose_goal_minimum = 90
            obj.postmeal_glucose_goal_maximum = 180
            obj.safe_zone_minimum = 60
            obj.safe_zone_maximum = 250
            obj.save()

        map(update, HealthInformation.objects.all())
        map(update, HealthProfessionalTargets.objects.all())
