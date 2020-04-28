import socket

from django.conf import settings
from django.core.management import call_command

from celery.task import task
from celery.task import periodic_task
from celery.schedules import crontab


@task
def post_processing(reading_id):
    from genesishealth.apps.logs.models import QALogEntry
    from genesishealth.apps.gdrives.models import GDrive
    from genesishealth.apps.readings.models import GlucoseReading
    reading = GlucoseReading.objects.get(pk=reading_id)
    # Update the patient's last glucose value
    if reading.patient:
        reading.patient.patient_profile.last_reading = reading
        reading.patient.patient_profile.save()
        partners = reading.patient.patient_profile.partners.filter(
            forward_readings=True)
        map(lambda x: x.queue_and_send_reading(reading), partners)
    else:
        if reading.device.status in (
                GDrive.DEVICE_STATUS_NEW, GDrive.DEVICE_STATUS_REPAIRABLE,
                GDrive.DEVICE_STATUS_REWORKED):
            QALogEntry.objects.create(
                meid=reading.device.meid,
                reading_datetime=reading.reading_datetime_utc,
                glucose_value=reading.glucose_value)
    reading.device.last_reading = reading
    reading.device.save()


@task
def forward_reading_to_partner(partner_id, attempt_id):
    from genesishealth.apps.api.models import (
        APIPartner, APIReadingForwardAttempt)
    from genesishealth.apps.readings.models import GlucoseReading
    attempt = APIReadingForwardAttempt.objects.get(pk=attempt_id)
    reading = attempt.reading
    if reading.measure_type == GlucoseReading.MEASURE_TYPE_TEST:
        return
    partner = APIPartner.objects.get(pk=partner_id)
    assert partner in reading.patient.patient_profile.partners.all()
    partner.send_glucose_reading(attempt)


@task
def forward_reading(reading_content):
    for info in settings.READING_FORWARD_URLS:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(
            (info['url'], info.get('port', settings.GDRIVE_READING_PORT))
        )
        s.sendall(reading_content)
        s.close()


@periodic_task(run_every=crontab(hour=0, minute=0))
def send_queued_readings():
    call_command('send_queued_readings')


@periodic_task(run_every=crontab(hour=0, minute=0))
def do_demo_readings():
    from django.contrib.auth.models import User
    for d in User.objects.filter(patient_profile__demo_patient=True,
                                 demo_profile__active=True):
        d.demo_profile.cron_process()
