from django import forms
from django.urls import reverse
from django.utils.timezone import get_default_timezone, now

from genesishealth.apps.accounts.models import GenesisGroup
from genesishealth.apps.epc.models.epc_order import EPCOrder
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.class_views.csv_report import (
    CSVReport, CSVReportForm, CSVReportView)
from genesishealth.apps.utils.request import require_admin_permission


test = require_admin_permission('orders')


class ConfigureShippingHistoryReportForm(CSVReportForm):
    start_date = forms.DateField()
    end_date = forms.DateField()
    companies = forms.ModelMultipleChoiceField(queryset=None)

    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop('group')
        super(ConfigureShippingHistoryReportForm, self).__init__(
            *args, **kwargs)
        self.fields['companies'].queryset = self.group.companies.all()

    def clean(self):
        data = super(ConfigureShippingHistoryReportForm, self).clean()
        if 'end_date' in data and data['start_date'] > data['end_date']:
            raise forms.ValidationError('Start date must be before end date.')
        return data

    def clean_end_date(self):
        tz = get_default_timezone()
        if self.cleaned_data['end_date'] > now().astimezone(tz).date():
            raise forms.ValidationError('End date cannot be in the future.')
        return self.cleaned_data['end_date']


class ShippingHistoryReport(CSVReport):
    header_rows = [[
        'GROUP ID #', 'GROUP NAME', 'ORDER ID', 'EPC ID', 'GHT ID',
        'INSURANCE ID', 'ORDER TYPE', 'METER', 'TEST STRIPS', 'LANCETS',
        'LANCING DEVICES', 'CONTROL SOLUTION', 'REQUESTED DATE',
        'PROCESSED DATE', 'SHIPPED DATE', 'ORDER STATUS', 'FULFILLMENT ID',
        'FULFILLMENT VENDOR NAME'
    ]]

    configuration_form_class = ConfigureShippingHistoryReportForm

    def configure(self, group_id):
        self.group = GenesisGroup.objects.get(pk=group_id)

    def get_configuration_form_kwargs(self):
        return {'group': self.group}

    def get_filename(self, data):
        return "export_shipping.csv"

    def get_header_rows(self, data):
        rows = [
            ['Shipping History Report for:', self.group.name],
            ['Date range:', '{start_date} - {end_date}'.format(**data)],
            []
        ]
        return rows + self.header_rows

    def get_queryset(self, data):
        return EPCOrder.objects.filter(
            epc_member__company__in=data['companies'],
            ship_date__range=(data['start_date'], data['end_date']))

    def get_rows(self, data):
        rows = []
        date_range = (data['start_date'], data['end_date'])
        for company in data['companies']:
            company_rows = [[company.id, company.name]]
            meter_total = strip_total = lancet_total = lancing_device_total = 0
            control_solution_total = 0
            orders = EPCOrder.objects.filter(
                epc_member__company=company,
                ship_date__range=date_range)
            order_rows = []
            for order in orders:
                # To keep format, we'll start with two blank cells.
                if order.epc_member.rx_partner is not None:
                    rx_partner_id = order.epc_member.rx_partner.epc_identifier
                    rx_partner_name = order.epc_member.rx_partner.name
                else:
                    rx_partner_id = 'N/A'
                    rx_partner_name = 'N/A'
                order_rows.append(
                    ['',
                     '',
                     order.order_number,
                     order.epc_member_identifier,
                     order.epc_member.user.id,
                     order.epc_member.insurance_identifier,
                     order.order_type,
                     order.meter_shipped,
                     order.strips_shipped,
                     order.lancets_shipped,
                     order.lancing_device_shipped,
                     order.control_solution_shipped,
                     order.order_date,
                     order.datetime_added.date(),
                     order.ship_date,
                     order.order_status,
                     rx_partner_id,
                     rx_partner_name]
                )
                if order.meter_shipped:
                    meter_total += order.meter_shipped
                if order.strips_shipped:
                    strip_total += order.strips_shipped
                if order.lancets_shipped:
                    lancet_total += order.lancets_shipped
                if order.lancing_device_shipped:
                    lancing_device_total += order.lancing_device_shipped
                if order.control_solution_shipped:
                    control_solution_total += order.control_solution_shipped
            # Add subtotal row
            company_rows.append([
                '',
                '',
                'SUB TOTALS',
                '',
                '',
                '',
                '',
                meter_total,
                strip_total,
                lancet_total,
                lancing_device_total,
                control_solution_total
            ])
            # Add orders
            company_rows.extend(order_rows)
            # Append and empty spacer row
            company_rows.append([])
            rows.extend(company_rows)
        return rows


class ShippingHistoryReportView(CSVReportView):
    page_title = "Shipping History Report"
    report_class = ShippingHistoryReport

    def get_breadcrumbs(self):
        group = self.get_group()
        return [
            Breadcrumb('Business Partners',
                       reverse('accounts:manage-groups')),
            Breadcrumb(
                'Business Partner: {0}'.format(group.name),
                reverse('accounts:manage-groups-detail',
                        args=[group.pk])),
            Breadcrumb(
                'Reports',
                reverse('accounts:manage-groups-reports',
                        args=[group.pk]))
        ]

    def get_group(self):
        return GenesisGroup.objects.get(pk=self.kwargs['group_id'])

    def get_post_data(self):  # pragma: no cover
        data = super(ShippingHistoryReportView, self).get_post_data()
        if not isinstance(data['companies'], list):
            data['companies'] = [data['companies']]
        return data

    def get_report_kwargs(self):
        return {'group_id': self.get_group().id}


group_export = test(
    ShippingHistoryReportView.as_view())
