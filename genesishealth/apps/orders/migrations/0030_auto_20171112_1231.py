# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-12 18:31
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0029_shippingpackagetype'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ordershipment',
            name='shipping_piece',
        ),
        migrations.AddField(
            model_name='ordershipment',
            name='package_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='orders.ShippingPackageType'),
        ),
        migrations.AlterField(
            model_name='ordershipment',
            name='package_height',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='ordershipment',
            name='package_length',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='ordershipment',
            name='package_width',
            field=models.FloatField(null=True),
        ),
    ]
