# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-13 00:42
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0030_auto_20171112_1231'),
    ]

    operations = [
        migrations.AddField(
            model_name='ordershipment',
            name='shipping_label_url',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='ordershipment',
            name='shipped_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='orders_shipped', to=settings.AUTH_USER_MODEL),
        ),
    ]
