# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-02-08 00:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0006_producttype_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='producttype',
            name='box_quantity',
            field=models.PositiveIntegerField(default=1),
        ),
    ]