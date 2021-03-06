# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-07-17 20:01
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0009_auto_20160716_1038'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScalabilityResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('response_time', models.FloatField()),
                ('is_success', models.BooleanField()),
                ('reading_server', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scalability_results', to='monitoring.ReadingServer')),
            ],
        ),
        migrations.CreateModel(
            name='ScalabilityTest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField()),
                ('duration', models.PositiveIntegerField()),
                ('date_started', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AddField(
            model_name='scalabilityresult',
            name='test',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='results', to='monitoring.ScalabilityTest'),
        ),
    ]
