# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-07-31 00:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0014_auto_20160701_1008'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activationrecord',
            name='reason',
            field=models.IntegerField(null=True),
        ),
    ]
