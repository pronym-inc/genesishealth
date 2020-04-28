from django.db import models


class OrderCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)
    is_refill = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name
