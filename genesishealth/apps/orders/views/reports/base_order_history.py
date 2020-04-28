from django import forms
from django.utils.timezone import get_default_timezone

from genesishealth.apps.utils.class_views.csv_report import (
    CSVReport, CSVReportForm, CSVReportView)


class ConfigureOrderHistoryReportForm(CSVReportForm):
    start_date = forms.DateField()
    end_date = forms.DateField()


class BaseOrderHistoryReport(CSVReport):
    header_rows = [[
        'Order Datetime', 'Order Type', 'Order Status', 'Patient',
        'Rx Partner', 'Date Shipped', 'Tracking Number', 'Invoice Number',
        'Strip Count', 'Meter Count', 'Lancet Count', 'Lancing Device Count',
        'Control Solution Count']]
    configuration_form_class = ConfigureOrderHistoryReportForm
    async_handle = "order_history"
    never_async = False

    def get_item_row(self, item):
        tz = get_default_timezone()
        if item.datetime_shipped:
            shipped_dt = item.datetime_shipped.astimezone(tz).date()
        else:
            shipped_dt = str(item.datetime_shipped)
        if item.patient is None:
            patient_str = 'N/A'
        else:
            patient_str = item.patient.get_reversed_name()
        if item.rx_partner is None:
            rx_str = 'N/A'
        else:
            rx_str = item.rx_partner.name
        return [
            item.datetime_added.astimezone(tz).date(),
            item.get_order_type_display(),
            item.get_order_status_display(),
            patient_str,
            rx_str,
            shipped_dt,
            item.get_tracking_number(),
            item.invoice_number,
            item.get_strips_quantity(),
            item.get_gdrive_quantity(),
            item.get_lancet_quantity(),
            item.get_lancing_device_quantity(),
            item.get_control_solution_quantity()
        ]


class BaseOrderHistoryReportView(CSVReportView):
    pass
