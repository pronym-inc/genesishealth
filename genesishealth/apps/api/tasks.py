from celery.schedules import crontab
from celery.task import periodic_task, task

from django.core.management import call_command


@task
def migrate_readings(patient_ids):
    from genesishealth.apps.accounts.models import PatientProfile
    users = PatientProfile.objects.get_users().filter(pk__in=patient_ids)
    for user in users:
        for partner in user.patient_profile.partners.all():
            partner.forward_patient_readings(user)


@periodic_task(run_every=crontab(hour=0, minute=0))
def send_daily_flatfiles():
    call_command('send_daily_flatfiles')
