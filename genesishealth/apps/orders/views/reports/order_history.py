from datetime import datetime, time, timedelta

from django import forms
from django.urls import reverse
from django.utils.timezone import get_default_timezone

from genesishealth.apps.accounts.models import Company, PatientProfile
from genesishealth.apps.orders.models import Order
from genesishealth.apps.pharmacy.models import PharmacyPartner
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.request import require_admin_permission

from .base_order_history import (
    ConfigureOrderHistoryReportForm, BaseOrderHistoryReport,
    BaseOrderHistoryReportView)


test = require_admin_permission('orders')


class ConfigureGlobalOrderHistoryReportForm(ConfigureOrderHistoryReportForm):
    start_date = forms.DateField()
    end_date = forms.DateField()
    employer = forms.ModelMultipleChoiceField(
        queryset=Company.objects.all(), required=False)
    rx_partner = forms.ModelMultipleChoiceField(
        queryset=PharmacyPartner.objects.all(), required=False,
        label='Pharmacy Partner')
    refill_method = forms.MultipleChoiceField(
        choices=PatientProfile.REFILL_METHOD_CHOICES, required=False)
    order_type = forms.ChoiceField(
        choices=Order.ORDER_TYPE_CHOICES, required=False)


class OrderHistoryReport(BaseOrderHistoryReport):
    configuration_form_class = ConfigureGlobalOrderHistoryReportForm

    def get_filename(self, data):
        return "order_history.csv"

    def get_queryset(self, data):
        tz = get_default_timezone()
        start = tz.localize(datetime.combine(data['start_date'], time()))
        end = tz.localize(
            datetime.combine(data['end_date'], time())) + timedelta(days=1)
        qs = Order.objects.filter(datetime_added__range=(start, end))
        if data['employer']:
            qs = qs.filter(
                patient__patient_profile__company__in=data['employer'])
        if data['rx_partner']:
            if data['order_type'] == Order.ORDER_TYPE_BULK:
                qs = qs.filter(rx_partner__in=data['rx_partner'])
            else:
                qs = qs.filter(
                    patient__patient_profile__rx_partner__in=data[
                        'rx_partner'])
        if data['refill_method']:
            qs = qs.filter(
                patient__patient_profile__refill_method__in=data[
                    'refill_method'])
        if data['order_type']:
            qs = qs.filter(order_type=data['order_type'])
        qs = qs.order_by('datetime_added')
        return qs


class OrderHistoryReportView(BaseOrderHistoryReportView):
    report_class = OrderHistoryReport

    def get_breadcrumbs(self):
        return [
            Breadcrumb("Reports", reverse("orders:reports-index", args=[]))]

    def get_page_title(self):
        return "Generate Order History"


main = test(OrderHistoryReportView.as_view())
