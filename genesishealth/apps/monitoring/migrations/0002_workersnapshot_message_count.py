# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-07-13 22:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='workersnapshot',
            name='message_count',
            field=models.PositiveIntegerField(null=True),
        ),
    ]