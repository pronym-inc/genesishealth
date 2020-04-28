# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-08-17 18:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gdrives', '0034_auto_20160816_2243'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gdrive',
            name='firmware_version',
        ),
        migrations.RemoveField(
            model_name='gdrive',
            name='module_version',
        ),
        migrations.AddField(
            model_name='gdrivemanufacturercarton',
            name='firmware_version',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='devices', to='gdrives.GDriveFirmwareVersion'),
        ),
        migrations.AddField(
            model_name='gdrivemanufacturercarton',
            name='module_version',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='devices', to='gdrives.GDriveModuleVersion'),
        ),
    ]
