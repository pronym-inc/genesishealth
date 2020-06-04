# Generated by Django 3.0.5 on 2020-06-01 04:44

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('health_information', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='healthinformation',
            name='compliance_goal',
            field=models.IntegerField(default=3, help_text='Number of required daily tests'),
        ),
        migrations.AlterField(
            model_name='healthprofessionaltargets',
            name='compliance_goal',
            field=models.IntegerField(default=3, help_text='Number of required daily tests'),
        ),
        migrations.AlterField(
            model_name='healthprofessionaltargets',
            name='patient',
            field=models.ForeignKey(limit_choices_to={'patient_profile__isnull': False}, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='healthprofessionaltargets',
            name='professional',
            field=models.ForeignKey(limit_choices_to={'professional_profile__isnull': False}, on_delete=django.db.models.deletion.CASCADE, related_name='custom_health_targets', to=settings.AUTH_USER_MODEL),
        ),
    ]
