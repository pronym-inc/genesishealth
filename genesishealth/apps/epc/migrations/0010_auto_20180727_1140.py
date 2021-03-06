# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-07-27 16:40
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('epc', '0009_auto_20180728_0829'),
    ]

    operations = [
        migrations.CreateModel(
            name='EPCOrderChange',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime_added', models.DateTimeField(auto_now_add=True)),
                ('epc_member_identifier', models.CharField(max_length=255, null=True)),
                ('order_number', models.CharField(max_length=255, null=True)),
                ('order_type', models.CharField(max_length=255, null=True)),
                ('order_method', models.CharField(max_length=255, null=True)),
                ('order_date', models.DateField(null=True)),
                ('control_solution_request', models.IntegerField(null=True)),
                ('meter_request', models.IntegerField(null=True)),
                ('strips_request', models.IntegerField(null=True)),
                ('lancet_request', models.IntegerField(null=True)),
                ('lancing_device_request', models.IntegerField(null=True)),
                ('pamphlet_id_request', models.IntegerField(null=True)),
                ('meter_shipped', models.IntegerField(null=True)),
                ('meid', models.CharField(max_length=255, null=True)),
                ('strips_shipped', models.IntegerField(null=True)),
                ('lancets_shipped', models.IntegerField(null=True)),
                ('control_solution_shipped', models.IntegerField(null=True)),
                ('lancing_device_shipped', models.IntegerField(null=True)),
                ('pamphlet_id_shipped', models.IntegerField(null=True)),
                ('order_status', models.CharField(max_length=255, null=True)),
                ('ship_date', models.DateField(null=True)),
                ('tracking_number', models.CharField(max_length=255, null=True)),
                ('epc_member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='epc_order_changes', to='epc.EPCMemberProfile')),
            ],
        ),
        migrations.RemoveField(
            model_name='epcorder',
            name='transaction',
        ),
        migrations.AddField(
            model_name='epcorder',
            name='original_transaction',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='epc_orders', to='epc.OrderRequestTransaction'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='epcorderchange',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='changes', to='epc.EPCOrder'),
        ),
        migrations.AddField(
            model_name='epcorderchange',
            name='transaction',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='order_change', to='epc.OrderRequestTransaction'),
        ),
    ]
