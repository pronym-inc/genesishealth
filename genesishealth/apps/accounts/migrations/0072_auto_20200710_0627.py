# Generated by Django 3.0.7 on 2020-07-10 11:21
import re

from django.db import migrations


def fix_phone_numbers(apps, schema_editor):
    PhoneNumber = apps.get_model('accounts', 'PhoneNumber')
    for pn in PhoneNumber.objects.all():
        new_phone = re.sub(r'[\(\)\- ]', '', pn.phone)
        if new_phone != pn.phone:
            pn.phone = new_phone
            pn.save()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0071_auto_20200601_0444'),
    ]

    operations = [
        migrations.RunPython(fix_phone_numbers)
    ]
