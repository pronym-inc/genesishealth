# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-08-13 01:21
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gdrives', '0028_auto_20160811_2101'),
    ]

    operations = [
        migrations.CreateModel(
            name='GDriveCarton',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='gdrive',
            name='carton_number',
        ),
        migrations.AddField(
            model_name='gdrive',
            name='carton',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='devices', to='gdrives.GDriveCarton', verbose_name=b'Warehouse carton'),
        ),
    ]
