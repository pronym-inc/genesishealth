# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-08-08 23:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gdrives', '0023_auto_20160808_1819'),
    ]

    operations = [
        migrations.AddField(
            model_name='gdrive',
            name='tray_number',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='gdrive',
            name='warehouse_number',
            field=models.CharField(max_length=255, null=True),
        ),
    ]