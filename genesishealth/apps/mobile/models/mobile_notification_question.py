from django.db import models


class MobileNotificationQuestion(models.Model):
    name = models.CharField(max_length=255, unique=True)
    text = models.TextField()
