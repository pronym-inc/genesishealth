# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-08-01 17:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('epc', '0015_epclogentry'),
    ]

    operations = [
        migrations.AlterField(
            model_name='epclogentry',
            name='response_sent',
            field=models.TextField(),
        ),
    ]
