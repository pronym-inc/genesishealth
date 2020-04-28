# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-07-01 12:48
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gdrives', '0004_auto_20160701_0740'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gdrivelogentry',
            name='reading',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='gdrive_log_entry', to='readings.GlucoseReading'),
        ),
        migrations.AlterField(
            model_name='gdrivetransmissionlogentry',
            name='associated_patient_profile',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.PatientProfile'),
        ),
        migrations.AlterField(
            model_name='gdrivetransmissionlogentry',
            name='reading',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='log_entry', to='readings.GlucoseReading'),
        ),
        migrations.AlterField(
            model_name='gdrivetransmissionlogentry',
            name='recovered_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]