from django.db import models
from django.utils.timezone import now


class MobileNotification(models.Model):
    profile = models.ForeignKey(
        'MobileProfile',
        on_delete=models.CASCADE,
        related_name='notifications',
        db_index=True,
        editable=False
    )
    datetime_created = models.DateTimeField(default=now, db_index=True)
    subject = models.TextField()
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    is_pushed = models.BooleanField(default=False, editable=False)

    class Meta:
        ordering = ['-datetime_created']

    def push_to_device(self) -> None:
        from genesishealth.apps.mobile.expo_client import ExpoNotificationClient
        client = ExpoNotificationClient()
        response = client.send_notification(self)
        if response.success:
            self.is_pushed = True
            self.save()
