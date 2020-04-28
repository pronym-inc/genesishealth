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
    ]

    operations = [
        migrations.CreateModel(
            name='BloodPressureReading',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reading_datetime', models.DateTimeField()),
                ('systolic_value', models.IntegerField()),
                ('diastolic_value', models.IntegerField()),
                ('device', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='readings', to='gdrives.BloodPressureDevice')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blood_pressure_readings', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BloodPressureReadingNote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(blank=True, default=b'')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('visible_to_patient', models.BooleanField(default=True, editable=False)),
                ('author', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('entry', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='notes', to='readings.BloodPressureReading')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GlucoseReading',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('measure_type', models.CharField(choices=[(b'normal', b'Normal'), (b'before_meal', b'Before meal'), (b'after_meal', b'After meal'), (b'test_mode', b'TEST mode')], default=b'normal', max_length=100)),
                ('reading_datetime_utc', models.DateTimeField()),
                ('reading_datetime_offset', models.IntegerField(default=0)),
                ('glucose_value', models.IntegerField()),
                ('committed', models.BooleanField(default=False)),
                ('in_use', models.BooleanField(default=False)),
                ('commit_attempts', models.IntegerField(default=0)),
                ('permanently_failed', models.BooleanField(default=False)),
                ('unique_id', models.CharField(blank=True, max_length=255)),
                ('alert_sent', models.BooleanField(default=False)),
                ('test_reading', models.BooleanField(default=False)),
                ('manually_changed_time', models.DateTimeField(null=True)),
                ('raw_data', models.TextField()),
                ('device', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='readings', to='gdrives.GDrive')),
                ('manually_changed_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='glucose_readings', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GlucoseReadingNote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(blank=True, default=b'')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('visible_to_patient', models.BooleanField(default=True, editable=False)),
                ('author', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('entry', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='notes', to='readings.GlucoseReading')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='WeightReading',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reading_datetime', models.DateTimeField()),
                ('value', models.IntegerField()),
                ('device', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='readings', to='gdrives.WeightDevice')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='weight_readings', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='WeightReadingNote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(blank=True, default=b'')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('visible_to_patient', models.BooleanField(default=True, editable=False)),
                ('author', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('entry', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='notes', to='readings.WeightReading')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterUniqueTogether(
            name='weightreadingnote',
            unique_together=set([('author', 'entry')]),
        ),
        migrations.AlterUniqueTogether(
            name='glucosereadingnote',
            unique_together=set([('author', 'entry')]),
        ),
        migrations.AlterUniqueTogether(
            name='bloodpressurereadingnote',
            unique_together=set([('author', 'entry')]),
        ),
    ]
