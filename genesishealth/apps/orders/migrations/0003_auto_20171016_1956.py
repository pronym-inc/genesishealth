# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2017-10-17 00:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_auto_20171016_1812'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='is_claim_approved',
            field=models.BooleanField(default=False),
        ),
    ]
