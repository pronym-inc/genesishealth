from django.db import models


class PatientNote(models.Model):
    """A note about a patient."""
    author = models.ForeignKey(
        'accounts.ProfessionalProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='patient_notes'
    )
    patient = models.ForeignKey(
        'accounts.PatientProfile',
        on_delete=models.CASCADE,
        related_name='patient_notes'
    )
    datetime_added = models.DateTimeField(auto_now_add=True)
    content = models.TextField()
