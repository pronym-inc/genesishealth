# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2017-10-19 04:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0005_auto_20171017_0837'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderShipmentBox',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('length', models.FloatField()),
                ('height', models.FloatField()),
                ('width', models.FloatField()),
            ],
        ),
        migrations.AddField(
            model_name='order',
            name='is_local',
            field=models.BooleanField(default=False),
        ),
    ]