# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2017-09-19 01:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0038_auto_20170918_1626'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adminprofile',
            name='permission_groups',
            field=models.ManyToManyField(blank=True, related_name='members', to='accounts.AdminPermissionGroup'),
        ),
        migrations.AlterField(
            model_name='adminprofile',
            name='permissions',
            field=models.ManyToManyField(blank=True, related_name='admin_users', to='accounts.AdminPermission'),
        ),
    ]