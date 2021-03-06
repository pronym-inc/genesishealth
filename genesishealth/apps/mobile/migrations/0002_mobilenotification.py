# Generated by Django 3.0.8 on 2020-08-30 21:46

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('mobile', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MobileNotification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('subject', models.CharField(max_length=255)),
                ('message', models.TextField()),
                ('is_read', models.BooleanField(default=False)),
                ('profile', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='mobile.MobileProfile')),
            ],
        ),
    ]
