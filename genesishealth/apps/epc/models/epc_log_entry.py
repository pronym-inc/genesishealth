from django.db import models
from django.utils.timezone import now


class EPCLogEntry(models.Model):
    TRANSACTION_TYPE_ORDER = 'order'
    TRANSACTION_TYPE_PATIENT = 'patient'

    TRANSACTION_TYPE_CHOICES = (
        (TRANSACTION_TYPE_ORDER, 'Order'),
        (TRANSACTION_TYPE_PATIENT, 'Patient')
    )

    datetime_added = models.DateTimeField(default=now)
    is_successful = models.BooleanField()
    content = models.TextField()
    source = models.CharField(max_length=255)
    transaction_type = models.CharField(
        max_length=255, choices=TRANSACTION_TYPE_CHOICES)
    response_sent = models.TextField()
    epc_member = models.ForeignKey('accounts.PatientProfile', null=True, on_delete=models.SET_NULL)

    class Meta:
        app_label = 'epc'

    def add_transaction(self, transaction):
        transaction.log_entry = self
        transaction.save()
        if transaction.epc_member:
            self.epc_member = transaction.epc_member
            self.save()
