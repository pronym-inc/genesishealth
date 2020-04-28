# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-08-31 21:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dropdowns', '0009_communicationstatus_is_closed'),
        ('gdrives', '0042_auto_20160823_1512'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gdrivecomplaint',
            name='problems',
        ),
        migrations.AddField(
            model_name='gdrivecomplaint',
            name='found_problems',
            field=models.ManyToManyField(related_name='_gdrivecomplaint_found_problems_+', to='dropdowns.DeviceProblem'),
        ),
        migrations.AddField(
            model_name='gdrivecomplaint',
            name='reported_problems',
            field=models.ManyToManyField(related_name='complaints', to='dropdowns.DeviceProblem'),
        ),
    ]
