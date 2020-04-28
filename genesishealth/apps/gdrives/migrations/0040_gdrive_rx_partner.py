# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-08-23 20:07
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gdrives', '0039_auto_20160823_1442'),
    ]

    operations = [
        migrations.AddField(
            model_name='gdrive',
            name='rx_partner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='devices', to='gdrives.PharmacyPartner'),
        ),
    ]
