from django.db import models
from django.utils.timezone import now


class PatientRequestTransaction(models.Model):
    log_transaction_type = 'patient'

    TRANSACTION_TYPE_CHOICES = (
        ('original', 'original'),
        ('update', 'update')
    )

    datetime_added = models.DateTimeField(default=now)
    submitted_username = models.CharField(max_length=255, null=True)
    authenticated_user = models.ForeignKey(
        'EPCAPIUser', null=True, related_name='patient_transactions', on_delete=models.SET_NULL)

    raw_request = models.TextField()

    transaction_identifier = models.CharField(max_length=255, null=True)
    transaction_type = models.CharField(
        max_length=255, choices=TRANSACTION_TYPE_CHOICES, null=True)
    epc_member_identifier = models.CharField(max_length=255)
    epc_member = models.ForeignKey(
        'accounts.PatientProfile', related_name='patient_request_transactions',
        null=True, on_delete=models.SET_NULL)
    group_identifier_raw = models.CharField(max_length=255, null=True)
    group_identifier = models.ForeignKey('accounts.Company', null=True, on_delete=models.SET_NULL)
    fulfillment_identifier_raw = models.CharField(max_length=255, null=True)
    fulfillment_identifier = models.ForeignKey(
        'pharmacy.PharmacyPartner', null=True, on_delete=models.SET_NULL)
    nursing_identifier_raw = models.CharField(max_length=255, null=True)
    nursing_identifier = models.ForeignKey('nursing.NursingGroup', null=True, on_delete=models.SET_NULL)

    first_name = models.CharField(max_length=255, null=True)
    last_name = models.CharField(max_length=255, null=True)
    address1 = models.CharField(max_length=255, null=True)
    address2 = models.CharField(max_length=255, null=True)
    city = models.CharField(max_length=255, null=True)
    state = models.CharField(max_length=255, null=True)
    zipcode = models.CharField(max_length=255, null=True)
    phone = models.CharField(max_length=255, null=True)
    date_of_birth = models.DateField(null=True)
    email_address = models.CharField(max_length=255, null=True)

    is_successful = models.BooleanField()

    log_entry = models.OneToOneField(
        'EPCLogEntry', null=True, related_name='patient_transaction', on_delete=models.SET_NULL)

    class Meta:
        app_label = 'epc'
