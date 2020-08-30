# Generated by Django 3.0.8 on 2020-08-30 21:47

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('mobile', '0002_mobilenotification'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mobilenotification',
            name='datetime_created',
            field=models.DateTimeField(db_index=True, default=django.utils.timezone.now),
        ),
    ]
