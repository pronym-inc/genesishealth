# Generated by Django 3.0.5 on 2020-06-01 04:44

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0003_auto_20180728_0741'),
        ('nursing', '0001_initial'),
        ('accounts', '0071_auto_20200601_0444'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('orders', '0048_auto_20190227_0543'),
        ('epc', '0020_epcorder_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='epclogentry',
            name='epc_member',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.PatientProfile'),
        ),
        migrations.AlterField(
            model_name='epclogentry',
            name='transaction_type',
            field=models.CharField(choices=[('order', 'Order'), ('patient', 'Patient')], max_length=255),
        ),
        migrations.AlterField(
            model_name='epcorder',
            name='order',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='epc_orders', to='orders.Order'),
        ),
        migrations.AlterField(
            model_name='epcordernote',
            name='added_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='epc_order_notes', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='epcordernote',
            name='order_change',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='note', to='epc.EPCOrderChange'),
        ),
        migrations.AlterField(
            model_name='orderrequesttransaction',
            name='authenticated_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order_transactions', to='epc.EPCAPIUser'),
        ),
        migrations.AlterField(
            model_name='orderrequesttransaction',
            name='log_entry',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order_transaction', to='epc.EPCLogEntry'),
        ),
        migrations.AlterField(
            model_name='orderrequesttransaction',
            name='transaction_type',
            field=models.CharField(choices=[('original', 'original'), ('update', 'update')], max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='patientrequesttransaction',
            name='authenticated_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='patient_transactions', to='epc.EPCAPIUser'),
        ),
        migrations.AlterField(
            model_name='patientrequesttransaction',
            name='epc_member',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='patient_request_transactions', to='accounts.PatientProfile'),
        ),
        migrations.AlterField(
            model_name='patientrequesttransaction',
            name='fulfillment_identifier',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='pharmacy.PharmacyPartner'),
        ),
        migrations.AlterField(
            model_name='patientrequesttransaction',
            name='group_identifier',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.Company'),
        ),
        migrations.AlterField(
            model_name='patientrequesttransaction',
            name='log_entry',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='patient_transaction', to='epc.EPCLogEntry'),
        ),
        migrations.AlterField(
            model_name='patientrequesttransaction',
            name='nursing_identifier',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='nursing.NursingGroup'),
        ),
        migrations.AlterField(
            model_name='patientrequesttransaction',
            name='transaction_type',
            field=models.CharField(choices=[('original', 'original'), ('update', 'update')], max_length=255, null=True),
        ),
    ]
