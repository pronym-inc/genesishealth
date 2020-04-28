# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-05-07 20:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('audit', '0002_auto_20160507_1530'),
    ]

    state_operations = [
        migrations.CreateModel(
            name='QALogEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime_created', models.DateTimeField(auto_now_add=True)),
                ('reading_datetime', models.DateTimeField()),
                ('glucose_value', models.IntegerField()),
                ('meid', models.CharField(max_length=255)),
            ],
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(state_operations=state_operations)
    ]
