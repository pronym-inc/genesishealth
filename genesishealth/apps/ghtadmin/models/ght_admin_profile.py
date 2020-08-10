from django.db import models

from solo.models import SingletonModel


class GhtAdminProfile(SingletonModel):
    billing_report_enabled = models.BooleanField(default=True)
    call_log_history_enabled = models.BooleanField(default=True)
    call_log_report_enabled = models.BooleanField(default=True)
    eligibility_file_enabled = models.BooleanField(default=True)
    meid_report_enabled = models.BooleanField(default=True)
    meter_deactivation_report_enabled = models.BooleanField(default=True)
    participation_status_report_enabled = models.BooleanField(default=True)
    shipping_history_enabled = models.BooleanField(default=True)
    target_range_report_enabled = models.BooleanField(default=True)
