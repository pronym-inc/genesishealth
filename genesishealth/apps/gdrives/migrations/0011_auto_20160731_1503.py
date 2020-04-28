# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-07-31 20:03
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gdrives', '0010_gdrivenonconformity'),
    ]

    operations = [
        migrations.AddField(
            model_name='gdrivecomplaint',
            name='rma_return_date',
            field=models.DateField(default=datetime.date(2016, 7, 31)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='gdrivenonconformity',
            name='device',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='non_conformities', to='gdrives.GDrive'),
            preserve_default=False,
        ),
    ]