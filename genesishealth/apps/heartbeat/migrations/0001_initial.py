# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-11-03 20:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EndToEndRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('result', models.CharField(choices=[(b'success', b'Success'), (b'failure', b'Failure'), (b'warning', b'Warning')], max_length=255)),
                ('message', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ['-datetime'],
            },
        ),
    ]
