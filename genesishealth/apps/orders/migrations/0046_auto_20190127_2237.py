# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-01-28 04:37
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0045_auto_20190106_1531'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ordershipment',
            name='shipped_date',
            field=models.DateField(default=django.utils.timezone.now),
        ),
    ]
