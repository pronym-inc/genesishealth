# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-08-03 01:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dropdowns', '0006_gdrivenonconformitytype'),
    ]

    operations = [
        migrations.AddField(
            model_name='producttype',
            name='description',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='producttype',
            name='manufacturer',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='producttype',
            name='unit',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
    ]
