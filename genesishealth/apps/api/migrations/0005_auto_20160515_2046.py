# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-05-16 01:46
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_auto_20160515_1956'),
    ]

    operations = [
        migrations.AddField(
            model_name='apiflatfileconnection',
            name='port',
            field=models.PositiveIntegerField(default=22, max_length=255),
        ),
        migrations.AlterField(
            model_name='apipartner',
            name='flatfile_connection',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.APIFlatfileConnection'),
        ),
    ]
