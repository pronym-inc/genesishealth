# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-07-26 12:52
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('epc', '0005_auto_20180712_2122'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderrequesttransaction',
            name='datetime_added',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
