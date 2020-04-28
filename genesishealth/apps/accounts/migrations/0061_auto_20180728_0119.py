# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-07-28 06:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nursing', '0001_initial'),
        ('accounts', '0060_auto_20180727_2344'),
    ]

    operations = [
        migrations.AddField(
            model_name='patientprofile',
            name='nursing_group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='patients', to='nursing.NursingGroup'),
        ),
        migrations.AlterField(
            model_name='company',
            name='payor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='companies', to='accounts.Payor'),
        ),
    ]
