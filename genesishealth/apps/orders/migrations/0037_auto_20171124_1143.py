# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-24 17:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0036_auto_20171124_1120'),
    ]

    operations = [
        migrations.AddField(
            model_name='shippingpackagetype',
            name='enabled',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='shippingpackagetype',
            name='name',
            field=models.CharField(choices=[(b'Postcard', b'Postcard'), (b'Letter', b'Letter'), (b'Large Envelope or Flat', b'Large Envelope or Flat'), (b'Thick Envelope', b'Thick Envelope'), (b'Package', b'Package'), (b'Small Flat Rate Box', b'Small Flat Rate Box'), (b'Flat Rate Box', b'Flat Rate Box'), (b'Flat Rate Envelope', b'Flat Rate Envelope'), (b'Flat Rate Padded Envelope', b'Flat Rate Padded Envelope'), (b'Large Package', b'Large Package'), (b'Oversized Package', b'Oversized Package'), (b'Regional Rate Box A', b'Regional Rate Box A'), (b'Regional Rate Box B', b'Regional Rate Box B'), (b'Regional Rate Box C', b'Regional Rate Box C'), (b'Legal Flat Rate Envelope', b'Legal Flat Rate Envelope')], max_length=255, unique=True),
        ),
    ]
