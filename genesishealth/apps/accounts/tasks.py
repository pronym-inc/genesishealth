from celery.schedules import crontab
from celery.task import periodic_task, task


@periodic_task(run_every=crontab(hour=1, minute=0))
def update_stat_averages():
    from genesishealth.apps.accounts.models import PatientProfile
    PatientProfile.objects.update_stat_averages()


@periodic_task(run_every=crontab(minute="*/2"))
def do_demo_readings():
    from django.contrib.auth.models import User
    for user in User.objects.filter(patient_profile__demo_patient=True,
                                    demo_profile__active=True):
        user.demo_profile.cron_process()


@task
def process_patient_form_data(patient_ids, user_id):
    from genesishealth.apps.accounts.models import PatientProfile
    from django.contrib.auth.models import User
    from genesishealth.apps.reports.models import TemporaryDownload
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return
    patients = User.objects.filter(id__in=patient_ids)
    content = PatientProfile.generate_csv2(patients)
    download = TemporaryDownload.objects.create(
        for_user=user, content=content, content_type='text/csv',
        filename='imported_patients.csv'
    )
    download.send_email("Your recently imported patients.")


@task
def process_patient_form_data_row(
        form_data, group_id, company_id=None, partner_id=None):
    from django.contrib.auth.models import User
    from genesishealth.apps.api.models import APIPartner
    from genesishealth.apps.accounts.models import GenesisGroup, Company
    from genesishealth.apps.accounts.forms.patients import (
        ImportPatientLineForm)
    form_kwargs = {}
    form_kwargs['supplied_username'] = form_data.pop('username', None)
    try:
        group = form_kwargs['initial_group'] = GenesisGroup.objects.get(
            pk=group_id)
    except GenesisGroup.DoesNotExist:
        return
    username = form_data.pop('username', None)
    if username:
        try:
            form_kwargs['instance'] = User.objects.filter(
                patient_profile__isnull=False).get(
                username=username)
        except User.DoesNotExist:
            return
    if company_id is not None:
        try:
            company = group.companies.get(id=company_id)
        except Company.DoesNotExist:
            return
    else:
        company = None
    if partner_id is not None:
        try:
            api_partner = APIPartner.objects.get(id=partner_id)
        except APIPartner.DoesNotExist:
            return
    else:
        api_partner = None
    form = ImportPatientLineForm(form_data, **form_kwargs)
    patient = form.save()
    group.add_patient(patient)
    if company:
        patient.patient_profile.company = company
    patient.patient_profile.save()
    if api_partner:
        patient.patient_profile.partners.add(api_partner)
    return patient.id


@task
def do_detect_timezone(patient_id):
    from django.conf import settings
    if settings.SKIP_DETECT_TIMEZONE:
        return
    from genesishealth.apps.accounts.models import PatientProfile
    profile = PatientProfile.objects.get(pk=patient_id)
    profile.detect_timezone()
