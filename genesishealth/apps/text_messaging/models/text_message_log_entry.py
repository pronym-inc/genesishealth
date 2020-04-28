from django.db import models


class TextMessageLogEntry(models.Model):
    recipients = models.ManyToManyField(
        'auth.User', related_name='text_message_log_entries')
    datetime_added = models.DateTimeField(auto_now_add=True)
    message = models.TextField()
    request_payload = models.TextField()
    response_content = models.TextField()
