# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-24 17:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0007_auto_20171023_2112'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ordershipmententry',
            name='quantity',
            field=models.PositiveIntegerField(default=1),
        ),
    ]
