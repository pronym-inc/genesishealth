# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-31 16:07
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0020_order_order_notes'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='delivery_priority',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='orders.DeliveryPriority'),
        ),
    ]
