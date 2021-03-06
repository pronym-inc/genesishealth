# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-08-12 02:01
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gdrives', '0027_auto_20160809_2100'),
    ]

    operations = [
        migrations.CreateModel(
            name='PharmacyPartner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.AlterField(
            model_name='gdrive',
            name='firmware_version',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='devices', to='gdrives.GDriveFirmwareVersion'),
        ),
    ]
