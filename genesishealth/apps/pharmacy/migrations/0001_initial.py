# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-27 03:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
    ]

    state_operations = [
        
    ]

    operations = [
        migrations.CreateModel(
            name='PharmacyPartner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True))
            ]
        )
    ]
