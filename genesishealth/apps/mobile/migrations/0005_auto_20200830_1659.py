# Generated by Django 3.0.8 on 2020-08-30 21:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mobile', '0004_auto_20200830_1648'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mobilenotification',
            name='subject',
        ),
        migrations.AddField(
            model_name='mobilenotification',
            name='is_pushed',
            field=models.BooleanField(default=False),
        ),
    ]
