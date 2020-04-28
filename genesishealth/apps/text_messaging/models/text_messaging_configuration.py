from django.db import models

from solo.models import SingletonModel


class TextMessagingConfiguration(SingletonModel):
    end_point_url_base = models.CharField(max_length=255)
    header_username = models.CharField(max_length=255)
    header_password = models.CharField(max_length=255)
    body_username = models.CharField(max_length=255)
    body_password = models.CharField(max_length=255)
    source_number = models.CharField(max_length=255)
    welcome_message = models.TextField()
    reminder_message = models.TextField()
    verify_ssl = models.BooleanField(default=True)
    is_qa_mode = models.BooleanField(default=True)
