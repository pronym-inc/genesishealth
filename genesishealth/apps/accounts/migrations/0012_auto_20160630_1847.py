# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-06-30 23:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_auto_20160630_1324'),
    ]

    operations = [
        migrations.AddField(
            model_name='patientstatisticrecord',
            name='average_value_last_180',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='patientstatisticrecord',
            name='readings_last_180',
            field=models.FloatField(null=True),
        ),
    ]
