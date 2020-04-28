# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-03-14 13:27
from __future__ import unicode_literals

from django.db import migrations


def update_rx_fields(apps, schema_editor):
    PatientProfile = apps.get_model("accounts", "PatientProfile")
    inherit_fields = {
        'bin_id': 'bin_number',
        'pcn_id': 'pcn_number',
        'glucose_strip_refill_frequency': 'glucose_strip_refill_frequency',
        'glucose_control_refill_frequency': 'glucose_control_refill_frequency',
        'lancing_refill_frequency': 'lancing_refill_frequency',
        'refill_method': 'refill_method',
        'billing_method': 'billing_method'
    }
    for profile in PatientProfile.objects.filter(company__isnull=False):
        company = profile.company
        save = False
        for company_field, profile_field in inherit_fields.iteritems():
            company_val = getattr(company, company_field)
            profile_val = getattr(profile, profile_field)
            if company_val is not None and profile_val != company_val:
                setattr(profile, profile_field, company_val)
                save = True
        if save:
            profile.save()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0055_auto_20180314_0827'),
    ]

    operations = [
        migrations.RunPython(update_rx_fields)
    ]
