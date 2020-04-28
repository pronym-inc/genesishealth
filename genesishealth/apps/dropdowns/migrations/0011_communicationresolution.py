# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2017-04-05 17:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dropdowns', '0010_meterdisposition'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommunicationResolution',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
    ]
