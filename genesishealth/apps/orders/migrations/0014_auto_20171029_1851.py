# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-29 23:51
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0001_initial'),
        ('orders', '0013_ordershipment_pharmacy_partner'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='invoice_number',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='rx_partner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='pharmacy.PharmacyPartner'),
        ),
        migrations.AlterField(
            model_name='order',
            name='order_origin',
            field=models.CharField(choices=[(b'account creation', b'Account Creation'), (b'manual', b'Manually Ordered'), (b'automatic refill', b'Automatic Refill'), (b'bulk order', b'Bulk Order')], max_length=255),
        ),
    ]
