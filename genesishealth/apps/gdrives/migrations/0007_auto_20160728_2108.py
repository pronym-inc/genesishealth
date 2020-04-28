# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-07-29 02:08
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gdrives', '0006_gdrivelogentry_reading_server'),
    ]

    operations = [
        migrations.CreateModel(
            name='GDriveFirmwareVersion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='GDriveLot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(max_length=255, unique=True)),
                ('manufactured_date', models.DateField()),
            ],
        ),
        migrations.AddField(
            model_name='gdrive',
            name='datetime_activated',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='gdrive',
            name='datetime_assigned',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='gdrive',
            name='datetime_status_changed',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='gdrive',
            name='status',
            field=models.CharField(blank=True, choices=[(b'new', b'New'), (b'active', b'Active'), (b'inactive', b'Inactive'), (b'suspended', b'Suspended')], editable=False, max_length=255),
        ),
        migrations.AddField(
            model_name='gdrive',
            name='firmware_version',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='devices', to='gdrives.GDriveFirmwareVersion'),
        ),
        migrations.AddField(
            model_name='gdrive',
            name='lot',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='devices', to='gdrives.GDriveLot'),
        ),
    ]
