from celery.schedules import crontab
from celery.task import periodic_task

from django.utils.timezone import now

from genesishealth.apps.accounts.models import PatientProfile
from genesishealth.apps.text_messaging.func import ConnectionsAPIClient
from genesishealth.apps.text_messaging.models import TextMessagingConfiguration


@periodic_task(run_every=crontab(hour=10, minute=0))
def send_welcome_texts():
    """Look for patients who:

    1) have a shipment sent more than 7 days ago
    2) have not received a welcome text"""
    config = TextMessagingConfiguration.get_solo()
    if config.is_qa_mode:
        return
    recipients = []
    for profile in PatientProfile.objects.filter(welcome_text_sent=False):
        for order in profile.user.orders.all():
            shipment = order.get_shipment()
            if shipment is None:
                continue
            days_ago = (now().date() - shipment.shipped_date).days
            if days_ago >= 7:
                recipients.append(profile.user)
                profile.welcome_text_sent = True
                profile.save()
    if len(recipients) == 0:
        return
    config = TextMessagingConfiguration.get_solo()
    client = ConnectionsAPIClient()
    client.send_text(config.welcome_message, recipients)
