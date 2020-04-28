# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-24 02:12
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('orders', '0006_auto_20171018_2348'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='added_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='orders_added', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='order',
            name='order_origin',
            field=models.CharField(choices=[(b'account creation', b'Account Creation'), (b'manual', b'Manually Ordered'), (b'automatic refill', b'Automatic Refill')], default='', max_length=255),
            preserve_default=False,
        ),
    ]