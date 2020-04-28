from django.conf import settings
from django.db import models


class EndToEndRecord(models.Model):
    E2E_RESULT_SUCCESS = 'success'
    E2E_RESULT_FAILURE = 'failure'
    E2E_RESULT_WARNING = 'warning'

    E2E_RESULT_CHOICES = (
        (E2E_RESULT_SUCCESS, 'Success'),
        (E2E_RESULT_FAILURE, 'Failure'),
        (E2E_RESULT_WARNING, 'Warning')
    )

    datetime = models.DateTimeField(auto_now_add=True)
    result = models.CharField(
        max_length=255,
        choices=E2E_RESULT_CHOICES
    )
    message = models.CharField(max_length=255)

    class Meta:
        ordering = ['-datetime']

    def get_previous_entries(self, amount):
        return EndToEndRecord.objects.filter(
            datetime__lt=self.datetime)[:amount]

    def is_critical(self):
        if self.result != self.E2E_RESULT_FAILURE:
            return False
        previous_entries = self.get_previous_entries(
            settings.E2E_CRITICAL_THRESHOLD)
        if previous_entries.count() < settings.E2E_CRITICAL_THRESHOLD:
            return False
        for entry in previous_entries:
            if entry.result != self.E2E_RESULT_FAILURE:
                return False
        return True

    def is_recovery(self):
        if self.result == self.E2E_RESULT_FAILURE:
            return False
        prev = self.get_previous_entries(1)
        if prev.count() == 0:
            return False
        previous_entry = prev[0]
        return previous_entry.is_critical()
