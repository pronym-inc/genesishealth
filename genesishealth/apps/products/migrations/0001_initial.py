# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-08-03 02:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dropdowns', '0008_auto_20160802_2109')
    ]

    state_operations = [
        migrations.CreateModel(
            name='ProductType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('part_number', models.CharField(max_length=255, unique=True)),
                ('unit', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('manufacturer', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=state_operations)
    ]
