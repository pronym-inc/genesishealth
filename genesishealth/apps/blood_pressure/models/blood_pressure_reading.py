from django.db import models
from django.utils.timezone import now


class BloodPressureReading(models.Model):
    patient_profile = models.ForeignKey(
        'accounts.PatientProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='blood_pressure_readings',
        editable=False
    )
    datetime_received = models.DateTimeField(default=now, editable=False)
    systolic_value = models.PositiveIntegerField()
    diastolic_value = models.PositiveIntegerField()
