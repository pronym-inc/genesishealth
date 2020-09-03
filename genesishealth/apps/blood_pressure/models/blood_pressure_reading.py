from django.db import models
from django.utils.timezone import now


class BloodPressureReading(models.Model):
    patient_profile = models.ForeignKey(
        'accounts.PatientProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='blood_pressure_readings',
        editable=False,
        db_index=True
    )
    datetime_received = models.DateTimeField(default=now, blank=True)
    systolic_value = models.PositiveIntegerField()
    diastolic_value = models.PositiveIntegerField()

    def send_notification(self) -> None:
        from genesishealth.apps.mobile.models import (
            MobileNotification, MobileNotificationQuestion, MobileNotificationQuestionEntry, MobileProfile)
        try:
            mobile_profile = self.patient_profile.user.mobile_profile
        except MobileProfile.DoesNotExist:
            return

        notification = MobileNotification.objects.create(
            profile=mobile_profile,
            subject="Your Blood Pressure Reading",
            message="Tell us some more information about your recent blood pressure reading.",
        )
        MobileNotificationQuestionEntry.objects.create(
            notification=notification,
            question=MobileNotificationQuestion.objects.get(pk=1)
        )
        notification.push_to_device()
