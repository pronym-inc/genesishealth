from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.urls import reverse
from django.db import models
from django.template.loader import render_to_string
from django.utils.timezone import now


def tomorrow_dt():
    return now() + timedelta(days=1)


def thirty_days_dt():
    return now() + timedelta(days=30)


class TemporaryDownload(models.Model):
    for_user = models.ForeignKey(User, related_name='temporary_downloads', on_delete=models.CASCADE)
    datetime_added = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField(
        null=True, default=thirty_days_dt)
    content = models.TextField()
    content_type = models.CharField(max_length=255)
    filename = models.CharField(max_length=255)

    def get_absolute_url(self):
        return "{}://{}{}".format(
            settings.HTTP_PROTOCOL,
            settings.SITE_URL,
            self.get_url())

    def get_url(self):
        return reverse('reports:temp-download', args=[self.id])

    def send_email(self, extra_message=None):
        ctx = {
            "extra_message": extra_message,
            "url": self.get_absolute_url()
        }
        subject = "MyGHR: Your download is ready."
        message = render_to_string("reports/temp_download_email.txt", ctx)
        eml = EmailMessage(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.DEFAULT_FROM_EMAIL],
            [self.for_user.email])
        eml.send()
