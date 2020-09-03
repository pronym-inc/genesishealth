from celery import shared_task


@shared_task
def push_to_device(notification_id: int) -> None:
    from genesishealth.apps.mobile.models import MobileNotification
    notification: MobileNotification = MobileNotification.objects.get(pk=notification_id)
    notification.push_to_device()
