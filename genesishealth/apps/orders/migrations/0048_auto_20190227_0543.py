# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-02-27 11:43
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0047_auto_20190127_2304'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ordershipment',
            name='packed_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='order_shipments_packed', to=settings.AUTH_USER_MODEL),
        ),
    ]
