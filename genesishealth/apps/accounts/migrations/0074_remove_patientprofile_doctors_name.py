# Generated by Django 3.0.8 on 2020-07-31 05:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0073_auto_20200720_2304'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='patientprofile',
            name='doctors_name',
        ),
    ]
