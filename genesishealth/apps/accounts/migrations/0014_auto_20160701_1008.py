# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-07-01 15:08
from __future__ import unicode_literals

from django.db import migrations
import genesishealth.apps.utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_previouspassword'),
    ]

    operations = [
        migrations.AlterField(
            model_name='demopatientprofile',
            name='reading_types',
            field=genesishealth.apps.utils.fields.SeparatedValuesField(),
        ),
    ]
