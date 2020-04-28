# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-01-19 18:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0005_producttype_is_refill'),
    ]

    operations = [
        migrations.AddField(
            model_name='producttype',
            name='category',
            field=models.CharField(choices=[(b'strips', b'Reading Strips'), (b'gdrive', b'Glucose Device'), (b'lancet', b'Lancets'), (b'lancing device', b'Lancing Device'), (b'control solution', b'Control Solution')], max_length=255, null=True, unique=True),
        ),
    ]