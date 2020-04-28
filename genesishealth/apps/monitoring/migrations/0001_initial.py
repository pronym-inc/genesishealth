# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-07-10 17:04
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DatabaseServer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('location', models.CharField(max_length=255, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DatabaseSnapshot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime_created', models.DateTimeField(auto_now_add=True)),
                ('short_load', models.FloatField()),
                ('medium_load', models.FloatField()),
                ('long_load', models.FloatField()),
                ('memory_free', models.PositiveIntegerField()),
                ('server', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='snapshots', to='monitoring.DatabaseServer')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MQSnapshot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime_created', models.DateTimeField(auto_now_add=True)),
                ('message_count', models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='ReadingServer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('location', models.CharField(max_length=255, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ReadingServerSnapshot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime_created', models.DateTimeField(auto_now_add=True)),
                ('short_load', models.FloatField()),
                ('medium_load', models.FloatField()),
                ('long_load', models.FloatField()),
                ('memory_free', models.PositiveIntegerField()),
                ('reading_response_time', models.FloatField()),
                ('server', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='snapshots', to='monitoring.ReadingServer')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='WebServer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('location', models.CharField(max_length=255, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='WebServerSnapshot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime_created', models.DateTimeField(auto_now_add=True)),
                ('short_load', models.FloatField()),
                ('medium_load', models.FloatField()),
                ('long_load', models.FloatField()),
                ('memory_free', models.PositiveIntegerField()),
                ('server', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='snapshots', to='monitoring.WebServer')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='WorkerServer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('location', models.CharField(max_length=255, unique=True)),
                ('is_queue_host', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='WorkerSnapshot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime_created', models.DateTimeField(auto_now_add=True)),
                ('short_load', models.FloatField()),
                ('medium_load', models.FloatField()),
                ('long_load', models.FloatField()),
                ('memory_free', models.PositiveIntegerField()),
                ('server', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='snapshots', to='monitoring.WorkerServer')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]