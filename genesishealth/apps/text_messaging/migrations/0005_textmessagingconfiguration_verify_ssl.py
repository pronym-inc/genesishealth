# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-04-13 18:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('text_messaging', '0004_textmessagingconfiguration_end_point_url_base'),
    ]

    operations = [
        migrations.AddField(
            model_name='textmessagingconfiguration',
            name='verify_ssl',
            field=models.BooleanField(default=True),
        ),
    ]
