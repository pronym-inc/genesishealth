# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-08-07 00:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gdrives', '0017_auto_20160806_1907'),
    ]

    operations = [
        migrations.AddField(
            model_name='gdrive',
            name='datetime_shipped',
            field=models.DateField(null=True),
        ),
    ]
