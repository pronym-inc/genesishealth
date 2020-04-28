from django.db import models


class ShippingPackageType(models.Model):
    TYPE_POSTCARD = 'Postcard'
    TYPE_LETTER = 'Letter'
    TYPE_L_ENVELOPE = 'Large Envelope or Flat'
    TYPE_THICK_ENVELOPE = 'Thick Envelope'
    TYPE_PACKAGE = 'Package'
    TYPE_S_FR_BOX = 'Small Flat Rate Box'
    TYPE_FR_BOX = 'Flat Rate Box'
    TYPE_FR_ENVELOPE = 'Flat Rate Envelope'
    TYPE_FR_P_ENVELOPE = 'Flat Rate Padded Envelope'
    TYPE_L_PACKAGE = 'Large Package'
    TYPE_OS_PACKAGE = 'Oversized Package'
    TYPE_RRA = 'Regional Rate Box A'
    TYPE_RRB = 'Regional Rate Box B'
    TYPE_RRC = 'Regional Rate Box C'
    TYPE_LFR_ENVELOPE = 'Legal Flat Rate Envelope'

    TYPE_CHOICES = (
        (TYPE_POSTCARD, 'Postcard'),
        (TYPE_LETTER, 'Letter'),
        (TYPE_L_ENVELOPE, 'Large Envelope or Flat'),
        (TYPE_THICK_ENVELOPE, 'Thick Envelope'),
        (TYPE_PACKAGE, 'Package'),
        (TYPE_S_FR_BOX, 'Small Flat Rate Box'),
        (TYPE_FR_BOX, 'Flat Rate Box'),
        (TYPE_FR_ENVELOPE, 'Flat Rate Envelope'),
        (TYPE_FR_P_ENVELOPE, 'Flat Rate Padded Envelope'),
        (TYPE_L_PACKAGE, 'Large Package'),
        (TYPE_OS_PACKAGE, 'Oversized Package'),
        (TYPE_RRA, 'Regional Rate Box A'),
        (TYPE_RRB, 'Regional Rate Box B'),
        (TYPE_RRC, 'Regional Rate Box C'),
        (TYPE_LFR_ENVELOPE, 'Legal Flat Rate Envelope')
    )

    name = models.CharField(max_length=255, unique=True, choices=TYPE_CHOICES)
    enabled = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name
