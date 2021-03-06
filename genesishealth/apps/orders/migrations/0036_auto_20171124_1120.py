# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-24 17:20
from __future__ import unicode_literals

from django.db import migrations


def create_shipping_classes(apps, schema_editor):
    ShippingClass = apps.get_model("orders", "ShippingClass")
    vals = [
        {'name': 'USPS First-Class Mail', 'stamps_abbreviation': 'US-FC'},
        {'name': 'USPS Priority Mail', 'stamps_abbreviation': 'US-PM'},
        {'name': 'USPS Priority Mail Express', 'stamps_abbreviation': 'US-XM'},
        {'name': 'USPS Media Mail', 'stamps_abbreviation': 'US-MM'},
        {'name': 'USPS Parcel Select', 'stamps_abbreviation': 'US-PS'},
        {'name': 'USPS Library Mail', 'stamps_abbreviation': 'US-LM'},
    ]
    for val in vals:
        ShippingClass.objects.create(**val)


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0035_shippingclass_enabled'),
    ]

    operations = [
        migrations.RunPython(create_shipping_classes)
    ]
