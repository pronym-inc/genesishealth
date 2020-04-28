import logging

from twilio.rest import Client

from django.conf import settings

logger = logging.getLogger(__name__)


def send_text_message(to, body):
    client = Client(settings.TWILIO_SID, settings.TWILIO_TOKEN)
    params = {
        "from_": settings.TWILIO_CALLERID,
        "to": to,
        "body": body
    }
    try:
        r = client.messages.create(**params)
        return r
    except Exception as e:
        logger.debug(params)
        logger.error(e)
        return False
