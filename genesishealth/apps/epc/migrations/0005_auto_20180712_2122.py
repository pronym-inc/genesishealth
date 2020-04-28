# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-07-13 02:22
from __future__ import unicode_literals

from django.db import migrations


def create_epc_test_entities(apps, schema_editor):  # pragma: no cover
    Company = apps.get_model("accounts", "Company")
    PharmacyPartner = apps.get_model("pharmacy", "PharmacyPartner")
    EPCAPIUser = apps.get_model("epc", "EPCAPIUser")
    EPCGroup = apps.get_model("epc", "EPCGroup")
    EPCNursingGroup = apps.get_model("epc", "EPCNursingGroup")
    EPCPharmacy = apps.get_model("epc", "EPCPharmacy")

    EPCAPIUser.objects.create(
        name="Test User",
        username="testuser",
        password="password123"
    )

    companies = Company.objects.all()
    if companies.count() > 0:
        company = companies[0]
        EPCGroup.objects.create(identifier='1234', company=company)

    pharmacies = PharmacyPartner.objects.all()
    if pharmacies.count() > 0:
        pharmacy = pharmacies[0]
        EPCPharmacy.objects.create(identifier='1234', pharmacy=pharmacy)

    EPCNursingGroup.objects.create(name="test", identifier="1234")


class Migration(migrations.Migration):

    dependencies = [
        ('epc', '0004_epcorder'),
    ]

    operations = [
        migrations.RunPython(create_epc_test_entities)
    ]


