# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-08-23 20:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gdrives', '0040_gdrive_rx_partner'),
    ]

    operations = [
        migrations.AddField(
            model_name='gdrive',
            name='datetime_shipped_to_rx_partner',
            field=models.DateTimeField(null=True),
        ),
    ]
