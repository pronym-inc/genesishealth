from django.db import models


class EPCAPIUser(models.Model):
    name = models.CharField(max_length=255, unique=True)
    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = 'epc'

    def __unicode__(self):  # pragma: no cover
        return self.name
