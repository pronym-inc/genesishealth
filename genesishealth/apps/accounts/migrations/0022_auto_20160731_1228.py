# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-07-31 17:28
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0021_auto_20160731_1154'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patientcommunicationnote',
            name='change_status_to',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='dropdowns.CommunicationStatus'),
        ),
    ]
