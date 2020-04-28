from django.core.management.base import BaseCommand

from genesishealth.apps.accounts.models import PatientProfile


class Command(BaseCommand):
    help = 'Sets last_glucose_value and last_reading_datetime for users.  Should only ever need to be run once.'

    def handle(self, **options):
        updated = 0
        not_updated = 0
        for profile in PatientProfile.objects.all():
            readings = profile.user.glucose_readings.order_by('-log_entry__datetime')
            if readings.count() > 1:
                profile.last_reading = readings[0]
                profile.save()
                updated += 1
            else:
                not_updated += 1
        print("Successfully updated {} patients.  Failed to update {} patients.".format(
            updated, not_updated))
