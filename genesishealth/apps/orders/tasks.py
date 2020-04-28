from celery.schedules import crontab
from celery.task import periodic_task

from genesishealth.apps.accounts.models import PatientProfile


@periodic_task(run_every=crontab(hour=2, minute=30))
def check_refills():
    from django.contrib.auth.models import User
    users = User.objects.filter(
        patient_profile__isnull=False,
        patient_profile__account_status=PatientProfile.ACCOUNT_STATUS_ACTIVE,
        patient_profile__group__exclude_from_orders=False)
    for user in users:
        user.patient_profile.check_for_refills()
