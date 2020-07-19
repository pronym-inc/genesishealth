from django import forms
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models import Q
from django.utils.timezone import now

from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.class_views.csv_report import (
    CSVReport, CSVReportForm, CSVReportView)
from genesishealth.apps.utils.request import require_admin_permission


test = require_admin_permission('orders')


class ConfigureProjectedRefillReportForm(CSVReportForm):
    REFILL_METHOD_ALL = 'all'
    REFILL_METHOD_CHOICES = (
        ('subscription', 'Subscription'),)

    refill_method = forms.ChoiceField(choices=REFILL_METHOD_CHOICES)


class ProjectedRefillReport(CSVReport):
    header_rows = [[
        'Patient', 'Insurance Identifier', 'Date of Birth',
        'Refill Method', 'MEID', 'Refill Amount (Boxes)',
        'Anticipated Refill Date']]
    configuration_form_class = ConfigureProjectedRefillReportForm

    def get_filename(self, data):
        return "projected_refill_{0}_{1}.csv".format(
            data['refill_method'],
            now().strftime('%Y_%m_%d'))

    def get_item_row(self, patient):
        device = patient.patient_profile.get_device()
        profile = patient.patient_profile
        refill_date = patient.patient_profile.get_anticipated_refill_date()
        if refill_date:
            refill_date_str = str(refill_date.date())
        else:
            refill_date_str = ''
        return [
            patient.get_reversed_name(),
            profile.insurance_identifier,
            profile.date_of_birth.strftime("%m/%d/%Y"),
            patient.patient_profile.get_refill_method(),
            device.meid,
            patient.patient_profile
            .get_strip_refill_amount_for_subscription_period(),
            refill_date_str
        ]

    def get_queryset(self, data):
        qs = User.objects.filter(
            patient_profile__isnull=False,
            gdrives__isnull=False)
        if (data['refill_method'] !=
                ConfigureProjectedRefillReportForm.REFILL_METHOD_ALL):
            qs = qs.filter(
                Q(patient_profile__refill_method__isnull=True,
                  patient_profile__company__refill_method=data['refill_method']) |  # noqa
                Q(patient_profile__refill_method=data['refill_method']))
        return qs


class ProjectedRefillReportView(CSVReportView):
    page_title = "Projected Refill Report"
    report_class = ProjectedRefillReport

    def _get_breadcrumbs(self):
        return [
            Breadcrumb("Reports", reverse("orders:reports-index", args=[]))
        ]


main = test(ProjectedRefillReportView.as_view())
