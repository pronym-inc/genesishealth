# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-08 02:43
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0049_patientprofile_rx_partner'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='patientprofile',
            name='last_refill_datetime',
        ),
    ]
