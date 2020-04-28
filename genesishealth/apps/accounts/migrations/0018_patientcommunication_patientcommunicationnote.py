# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-07-31 13:43
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dropdowns', '0003_communicationcategory_communicationstatus_producttype'),
        ('accounts', '0017_auto_20160731_0824'),
    ]

    operations = [
        migrations.CreateModel(
            name='PatientCommunication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=255)),
                ('datetime_added', models.DateTimeField(auto_now_add=True)),
                ('added_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='communications_added', to=settings.AUTH_USER_MODEL)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='communications', to='dropdowns.CommunicationCategory')),
                ('patient', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='communications', to=settings.AUTH_USER_MODEL)),
                ('status', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='dropdowns.CommunicationStatus')),
            ],
        ),
        migrations.CreateModel(
            name='PatientCommunicationNote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime_added', models.DateTimeField(auto_now_add=True)),
                ('content', models.TextField()),
                ('added_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='communication_notes', to=settings.AUTH_USER_MODEL)),
                ('change_status_to', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='dropdowns.CommunicationStatus')),
                ('replacements', models.ManyToManyField(related_name='_patientcommunicationnote_replacements_+', to='dropdowns.ProductType')),
            ],
        ),
    ]
