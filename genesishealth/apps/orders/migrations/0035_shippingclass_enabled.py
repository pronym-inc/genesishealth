# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-24 17:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0034_delete_deliverypriority'),
    ]

    operations = [
        migrations.AddField(
            model_name='shippingclass',
            name='enabled',
            field=models.BooleanField(default=True),
        ),
    ]
