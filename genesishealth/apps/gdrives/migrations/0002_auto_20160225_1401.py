# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-25 20:01
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('gdrives', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0002_auto_20160225_1401'),
        ('readings', '0001_initial'),
        ('accounts', '0002_auto_20160225_1401'),
    ]

    operations = [
        migrations.AddField(
            model_name='gdrivetransmissionlogentry',
            name='reading',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='log_entry', to='readings.GlucoseReading'),
        ),
        migrations.AddField(
            model_name='gdrivetransmissionlogentry',
            name='recovered_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='gdrivelogentry',
            name='device',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='gdrives.GDrive'),
        ),
        migrations.AddField(
            model_name='gdrivelogentry',
            name='reading',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='gdrive_log_entry', to='readings.GlucoseReading'),
        ),
        migrations.AddField(
            model_name='gdrive',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='gdrives', to='accounts.GenesisGroup'),
        ),
        migrations.AddField(
            model_name='gdrive',
            name='last_assigned_patient',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='gdrive',
            name='partner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='gdrives', to='api.APIPartner'),
        ),
        migrations.AddField(
            model_name='gdrive',
            name='patient',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='gdrives', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='gdrive',
            name='professional',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='child_gdrives', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='gdrive',
            name='unassigned_patients',
            field=models.ManyToManyField(related_name='previous_devices', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='gdrive',
            name='verizon_patient',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='verizon_devices', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='bloodpressuredevice',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='blood_pressure_devices', to='accounts.GenesisGroup'),
        ),
        migrations.AddField(
            model_name='bloodpressuredevice',
            name='patient',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='blood_pressure_devices', to=settings.AUTH_USER_MODEL),
        ),
    ]
