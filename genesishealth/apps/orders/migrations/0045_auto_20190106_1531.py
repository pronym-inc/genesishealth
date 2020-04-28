# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-01-06 21:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0044_auto_20190106_1225'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shippingclass',
            name='stamps_abbreviation',
            field=models.CharField(blank=True, choices=[(b'US-FC', b'US-FC'), (b'US-PM', b'US-PM'), (b'US-XM', b'US-XM'), (b'US-MM', b'US-MM'), (b'US-PS', b'US-PS'), (b'US-LM', b'US-LM')], max_length=255, null=True, unique=True),
        ),
    ]