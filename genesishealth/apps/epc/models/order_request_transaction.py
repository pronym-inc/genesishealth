from django.db import models
from django.utils.timezone import now


class OrderRequestTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = (
        ('original', 'original'),
        ('update', 'update')
    )

    datetime_added = models.DateTimeField(default=now)
    submitted_username = models.CharField(max_length=255, null=True)
    authenticated_user = models.ForeignKey(
        'EPCAPIUser', null=True, related_name='order_transactions', on_delete=models.SET_NULL)

    raw_request = models.TextField()

    epc_member = models.ForeignKey(
        'accounts.PatientProfile', related_name='order_request_transactions', on_delete=models.CASCADE)

    transaction_identifier = models.CharField(max_length=255, null=True)
    transaction_type = models.CharField(
        max_length=255, choices=TRANSACTION_TYPE_CHOICES, null=True)
    epc_member_identifier = models.CharField(max_length=255, null=True)
    order_number = models.CharField(max_length=255, null=True)
    order_type = models.CharField(max_length=255, null=True)
    order_method = models.CharField(max_length=255, null=True)
    order_date = models.DateField(null=True)
    control_solution_request = models.IntegerField(null=True)
    meter_request = models.IntegerField(null=True)
    strips_request = models.IntegerField(null=True)
    lancet_request = models.IntegerField(null=True)
    lancing_device_request = models.IntegerField(null=True)
    pamphlet_id_request = models.IntegerField(null=True)
    meter_shipped = models.IntegerField(null=True)
    meid = models.CharField(max_length=255, null=True)
    strips_shipped = models.IntegerField(null=True)
    lancets_shipped = models.IntegerField(null=True)
    control_solution_shipped = models.IntegerField(null=True)
    lancing_device_shipped = models.IntegerField(null=True)
    pamphlet_id_shipped = models.IntegerField(null=True)
    order_status = models.CharField(max_length=255, null=True)
    ship_date = models.DateField(null=True)
    tracking_number = models.CharField(max_length=255, null=True)

    log_entry = models.OneToOneField(
        'EPCLogEntry', null=True, related_name='order_transaction', on_delete=models.SET_NULL)

    is_successful = models.BooleanField()

    class Meta:
        app_label = 'epc'
