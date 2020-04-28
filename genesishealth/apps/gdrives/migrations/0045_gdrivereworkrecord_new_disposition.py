# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2017-04-04 05:06
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dropdowns', '0010_meterdisposition'),
        ('gdrives', '0044_gdrive_segregation_disposition'),
    ]

    operations = [
        migrations.AddField(
            model_name='gdrivereworkrecord',
            name='new_disposition',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='dropdowns.MeterDisposition'),
        ),
    ]
