# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-07-28 23:04
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0061_auto_20180728_0119'),
    ]

    operations = [
        migrations.RenameField(
            model_name='patientprofile',
            old_name='rh_member_id',
            new_name='epc_member_identifier',
        ),
    ]