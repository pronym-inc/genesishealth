# Generated by Django 3.0.8 on 2020-08-30 21:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mobile', '0003_auto_20200830_1647'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='mobilenotification',
            options={'ordering': ['-datetime_created']},
        ),
    ]