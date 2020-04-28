# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-07-31 14:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dropdowns', '0003_communicationcategory_communicationstatus_producttype'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommunicationSubcategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name_plural': 'Communication subcategories',
            },
        ),
        migrations.AlterModelOptions(
            name='communicationcategory',
            options={'ordering': ('name',), 'verbose_name_plural': 'Communication categories'},
        ),
        migrations.AlterModelOptions(
            name='communicationstatus',
            options={'ordering': ('name',), 'verbose_name_plural': 'Communication statuses'},
        ),
        migrations.AlterModelOptions(
            name='producttype',
            options={'ordering': ('name',)},
        ),
        migrations.RenameField(
            model_name='producttype',
            old_name='part_numbers',
            new_name='part_number',
        ),
        migrations.AddField(
            model_name='communicationsubcategory',
            name='category',
            field=models.ManyToManyField(related_name='subcategories', to='dropdowns.CommunicationStatus'),
        ),
    ]
