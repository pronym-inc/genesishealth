from datetime import timedelta

from celery.schedules import crontab
from celery.task import periodic_task

from django.utils.timezone import now

from genesishealth.apps.gdrives.models import GDrive
from genesishealth.apps.text_messaging.func import ConnectionsAPIClient
from genesishealth.apps.text_messaging.models import TextMessagingConfiguration


@periodic_task(run_every=crontab(hour=10, minute=0))
def send_reminder_texts():
    """Look for patients who:

    1) have received a device more than 7 days ago
    2) and took no readings with that device
    3) and have not had a reminder sent for that device"""
    config = TextMessagingConfiguration.get_solo()
    if config.is_qa_mode:
        return
    recipients = []
    seven_days_ago = (now() - timedelta(days=7)).date()
    for device in GDrive.objects.filter(
            shipment__isnull=False,
            reminder_text_sent=False,
            shipment__shipped_date__lte=seven_days_ago):
        # See if device has any readings.
        if device.readings.count() == 0:
            recipients.append(device.patient)
            device.reminder_text_sent = True
            device.save()

    if len(recipients) == 0:
        return
    client = ConnectionsAPIClient()
    client.send_text(config.reminder_message, recipients)
