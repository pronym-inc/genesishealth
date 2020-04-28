# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-07-28 12:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0002_auto_20171120_1816'),
    ]

    operations = [
        migrations.AddField(
            model_name='pharmacypartner',
            name='contact_name',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='pharmacypartner',
            name='epc_identifier',
            field=models.CharField(max_length=255, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='pharmacypartner',
            name='phone_number',
            field=models.CharField(max_length=255, null=True),
        ),
    ]