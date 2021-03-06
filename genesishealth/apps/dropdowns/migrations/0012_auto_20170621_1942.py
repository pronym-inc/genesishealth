# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2017-06-22 00:42
from __future__ import unicode_literals

from django.db import migrations


def add_device_statuses(apps, schema_editor):
    MeterDisposition = apps.get_model('dropdowns', 'MeterDisposition')
    names = [
        'Ready for re-inspection',
        'Returned to Vendor',
        'Reworked by Employee',
        'Reworked by Vendor',
        'Segregate for Destruction',
        'Segregate for Rework'
    ]
    for name in names:
        MeterDisposition.objects.get_or_create(name=name)


class Migration(migrations.Migration):

    dependencies = [
        ('dropdowns', '0011_communicationresolution'),
    ]

    operations = [
        migrations.RunPython(add_device_statuses)
    ]
