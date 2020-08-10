from django import forms
from django.contrib.auth.decorators import user_passes_test

from genesishealth.apps.utils.class_views import GenesisFormView
from genesishealth.apps.utils.forms import GenesisForm
from genesishealth.apps.utils.request import admin_user


class ReportsForm(GenesisForm):
    billing_report = forms.BooleanField(required=False)
    call_log_history = forms.BooleanField(required=False)
    call_log_report = forms.BooleanField(required=False)
    eligibility_file = forms.BooleanField(required=False)
    meid_report = forms.BooleanField(required=False)
    meter_deactivation_report = forms.BooleanField(required=False)
    participation_status_report = forms.BooleanField(required=False)
    shipping_history = forms.BooleanField(required=False)
    target_range_report = forms.BooleanField(required=False)


class ReportsFormView(GenesisFormView):
    form_class = ReportsForm
    page_title = "Manage Reports"


main = user_passes_test(admin_user)(ReportsFormView.as_view())
