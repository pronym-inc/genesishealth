# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-08-18 18:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dropdowns', '0009_communicationstatus_is_closed'),
        ('gdrives', '0036_auto_20160818_1232'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gdrivenonconformity',
            name='non_conformity_type',
        ),
        migrations.AddField(
            model_name='gdrivenonconformity',
            name='non_conformity_types',
            field=models.ManyToManyField(related_name='_gdrivenonconformity_non_conformity_types_+', to='dropdowns.GDriveNonConformityType'),
        ),
    ]
