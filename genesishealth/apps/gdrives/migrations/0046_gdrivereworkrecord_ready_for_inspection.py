# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2017-04-19 18:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gdrives', '0045_gdrivereworkrecord_new_disposition'),
    ]

    operations = [
        migrations.AddField(
            model_name='gdrivereworkrecord',
            name='ready_for_inspection',
            field=models.BooleanField(default=False),
        ),
    ]