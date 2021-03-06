# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-01-13 23:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0066_genesisgroup_should_generate_refill_files'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patientcommunication',
            name='subject',
            field=models.CharField(choices=[(b'inbound_epc', b'Inbound call EPC'), (b'inbound_other', b'Inbound call other'), (b'inbound_email', b'Inbound email'), (b'outbound', b'Outbound call')], max_length=255),
        ),
    ]
