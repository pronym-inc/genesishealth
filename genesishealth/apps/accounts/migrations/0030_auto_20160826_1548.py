# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-08-26 20:48
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0029_remove_patientcommunication_is_closed'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='patientcommunicationnote',
            options={'ordering': ('-datetime_added',)},
        ),
    ]
