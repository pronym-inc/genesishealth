from django.db import models


class OrderShipmentBox(models.Model):
    name = models.CharField(max_length=255, unique=True)
    length = models.FloatField()
    height = models.FloatField()
    width = models.FloatField()
