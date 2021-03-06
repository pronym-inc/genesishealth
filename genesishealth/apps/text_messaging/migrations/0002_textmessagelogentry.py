# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-03-29 18:44
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('text_messaging', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TextMessageLogEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime_added', models.DateTimeField(auto_now_add=True)),
                ('message', models.TextField()),
                ('phone_number', models.CharField(max_length=255)),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='text_message_log_entries', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
