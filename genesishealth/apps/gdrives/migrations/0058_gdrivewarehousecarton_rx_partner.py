# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-01-14 10:22
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0003_auto_20180728_0741'),
        ('gdrives', '0057_auto_20181217_1812'),
    ]

    operations = [
        migrations.AddField(
            model_name='gdrivewarehousecarton',
            name='rx_partner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='warehouse_cartons', to='pharmacy.PharmacyPartner'),
        ),
    ]