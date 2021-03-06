from django.db import models
from django.utils.timezone import now


class NursingQueueEntry(models.Model):
    """An entry that will go into the working queue for nursing users, to manage their patients."""
    ENTRY_TYPE_READINGS_TOO_LOW = 'readings too low'
    ENTRY_TYPE_READINGS_TOO_HIGH = 'readings too high'
    ENTRY_TYPE_NOT_ENOUGH_RECENT_READINGS = 'not enough recent readings'

    ENTRY_TYPE_CHOICES = (
        (ENTRY_TYPE_READINGS_TOO_LOW, 'Low Reading'),
        (ENTRY_TYPE_READINGS_TOO_HIGH, 'High Reading'),
        (ENTRY_TYPE_NOT_ENOUGH_RECENT_READINGS, 'No Reading')
    )
    patient = models.ForeignKey(
        'accounts.PatientProfile',
        on_delete=models.CASCADE,
        related_name='nursing_queue_entries'
    )
    entry_type = models.CharField(max_length=255, choices=ENTRY_TYPE_CHOICES)
    datetime_added = models.DateTimeField(default=now)
    due_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    completed_datetime = models.DateTimeField(null=True)
