# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-07-26 14:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('epc', '0006_auto_20180726_0752'),
    ]

    operations = [
        migrations.AddField(
            model_name='epcorder',
            name='control_solution_request',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='orderrequesttransaction',
            name='control_solution_request',
            field=models.IntegerField(null=True),
        ),
    ]