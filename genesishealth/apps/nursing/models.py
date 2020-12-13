from django.db import models
from django.db.models import Q


class NursingGroup(models.Model):
    name = models.CharField(max_length=255, unique=True)
    address = models.CharField(max_length=255)
    address2 = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255)
    zip = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    contact_name = models.CharField(max_length=255, null=True)
    phone_number = models.CharField(max_length=255, null=True)
    epc_identifier = models.CharField(max_length=255, null=True, unique=True)

    def __str__(self) -> str:
        return self.name

    def get_full_address(self):
        output = self.address
        if self.address2:
            output += " / {0}".format(self.address2)
        return output

    def get_nursing_queue_entries(self):
        from genesishealth.apps.nursing_queue.models import NursingQueueEntry
        x = (
            Q(patient__nursing_group=self) |
            Q(patient__nursing_group__isnull=True,
              patient__company__nursing_group=self) |
            Q(patient__nursing_group__isnull=True,
              patient__company__nursing_group__isnull=True,
              patient__group__nursing_group=self)
        )
        return NursingQueueEntry.objects.filter(
            (Q(entry_type=NursingQueueEntry.ENTRY_TYPE_NOT_ENOUGH_RECENT_READINGS) & (
                    (x & Q(patient__company__compliance_nursing_group__isnull=True)) |
                    Q(patient__company__compliance_nursing_group=self)
            )) |
            (Q(entry_type__in=(
                NursingQueueEntry.ENTRY_TYPE_READINGS_TOO_LOW,
                NursingQueueEntry.ENTRY_TYPE_READINGS_TOO_HIGH)) & x
            )
        )
