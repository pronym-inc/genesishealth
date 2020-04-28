# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2017-09-26 00:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0041_genesisgroup_skip_device_deactivation'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='billing_method',
            field=models.CharField(choices=[(b'medical', b'Medical'), (b'pharmacy', b'Pharmacy')], max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='bin_id',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='minimum_refill_quantity',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='pcn_id',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='refill_method',
            field=models.CharField(choices=[(b'subscription', b'Subscription'), (b'utilization', b'Utilization'), (b'employee_family', b'GHT Employee Family'), (b'demo', b'None / Demo')], max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='start_kit_size',
            field=models.IntegerField(null=True),
        ),
    ]
