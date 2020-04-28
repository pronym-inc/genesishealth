# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-01-13 20:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_producttype_is_bulk'),
    ]

    operations = [
        migrations.AddField(
            model_name='producttype',
            name='is_refill',
            field=models.BooleanField(default=False, verbose_name=b'Strip refill item'),
        ),
    ]