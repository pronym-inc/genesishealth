# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-08-07 04:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gdrives', '0019_auto_20160806_1947'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gdrive',
            name='device_id',
            field=models.CharField(max_length=100, unique=True),
        ),
    ]
