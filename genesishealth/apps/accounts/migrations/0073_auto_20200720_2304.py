# Generated by Django 3.0.8 on 2020-07-21 04:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0072_auto_20200710_0627'),
    ]

    operations = [
        migrations.AddField(
            model_name='patientprofile',
            name='doctors_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='phonenumber',
            name='contact',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='phone_numbers', to='accounts.Contact'),
        ),
    ]
