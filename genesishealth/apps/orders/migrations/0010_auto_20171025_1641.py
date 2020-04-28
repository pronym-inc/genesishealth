# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-25 21:41
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dropdowns', '0015_orderproblemcategory'),
        ('orders', '0009_auto_20171024_2125'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='problem_category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='dropdowns.OrderProblemCategory'),
        ),
        migrations.AddField(
            model_name='order',
            name='problem_description',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
    ]