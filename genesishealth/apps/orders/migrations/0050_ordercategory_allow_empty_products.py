# Generated by Django 3.0.8 on 2020-08-09 22:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0049_auto_20200601_0444'),
    ]

    operations = [
        migrations.AddField(
            model_name='ordercategory',
            name='allow_empty_products',
            field=models.BooleanField(default=False),
        ),
    ]
