from django.db import models


class ShippingClass(models.Model):
    STAMPS_ABBREVIATION_FC = 'US-FC'
    STAMPS_ABBREVIATION_PM = 'US-PM'
    STAMPS_ABBREVIATION_XM = 'US-XM'
    STAMPS_ABBREVIATION_MM = 'US-MM'
    STAMPS_ABBREVIATION_PS = 'US-PS'
    STAMPS_ABBREVIATION_LM = 'US-LM'

    STAMPS_ABBREVIATION_CHOICES = (
        (STAMPS_ABBREVIATION_FC, STAMPS_ABBREVIATION_FC),
        (STAMPS_ABBREVIATION_PM, STAMPS_ABBREVIATION_PM),
        (STAMPS_ABBREVIATION_XM, STAMPS_ABBREVIATION_XM),
        (STAMPS_ABBREVIATION_MM, STAMPS_ABBREVIATION_MM),
        (STAMPS_ABBREVIATION_PS, STAMPS_ABBREVIATION_PS),
        (STAMPS_ABBREVIATION_LM, STAMPS_ABBREVIATION_LM)
    )

    name = models.CharField(max_length=255, unique=True)
    stamps_abbreviation = models.CharField(
        max_length=255,
        unique=True,
        choices=STAMPS_ABBREVIATION_CHOICES,
        null=True,
        blank=True)
    enabled = models.BooleanField(default=True)
    is_for_bulk = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name
