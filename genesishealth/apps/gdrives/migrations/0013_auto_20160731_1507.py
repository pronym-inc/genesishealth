# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-07-31 20:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gdrives', '0012_gdrivecomplaint_is_validated'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gdrivecomplaint',
            name='rma_return_date',
            field=models.DateField(null=True),
        ),
    ]
