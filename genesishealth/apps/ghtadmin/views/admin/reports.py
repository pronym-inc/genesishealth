from typing import Any, Dict

from django import forms
from django.contrib.auth.decorators import user_passes_test

from genesishealth.apps.ghtadmin.models.ght_admin_profile import GhtAdminProfile
from genesishealth.apps.utils.class_views import GenesisFormView
from genesishealth.apps.utils.forms import GenesisModelForm
from genesishealth.apps.utils.request import admin_user


class ReportsForm(GenesisModelForm):
    class Meta:
        model = GhtAdminProfile
        fields = (
            'billing_report_enabled', 'call_log_history_enabled', 'call_log_report_enabled',
            'eligibility_file_enabled', 'meid_report_enabled', 'meter_deactivation_report_enabled',
            'participation_status_report_enabled', 'shipping_history_enabled', 'target_range_report_enabled'
        )


class ReportsFormView(GenesisFormView):
    form_class = ReportsForm
    page_title = "Manage Reports"

    def get_form_kwargs(self) -> Dict[str, Any]:
        return {
            'instance': GhtAdminProfile.get_solo()
        }


main = user_passes_test(admin_user)(ReportsFormView.as_view())
