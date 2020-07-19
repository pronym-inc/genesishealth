from urllib.parse import urlencode

from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse
from django.utils.timezone import now

from genesishealth.apps.dropdowns.models import DeviceProblem
from genesishealth.apps.gdrives.breadcrumbs import get_device_breadcrumbs
from genesishealth.apps.gdrives.forms import (
    GDriveComplaintForm, RMAInspectionForm, RMASummaryConfigureForm)
from genesishealth.apps.gdrives.models import GDriveComplaint
from genesishealth.apps.gdrives.views.base import GetDeviceMixin
from genesishealth.apps.reports.views.main import (
    ReportView, PDFPrintURLResponse)
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.class_views import (
    ActionTableColumn, ActionItem, AttributeTableColumn,
    GenesisAboveTableButton, GenesisFormView, GenesisTableLink,
    GenesisTableLinkAttrArg, GenesisTableView)
from genesishealth.apps.utils.request import admin_user


class GDriveComplaintTableView(GenesisTableView, GetDeviceMixin):
    def create_columns(self):
        device = self.get_device()
        return [
            AttributeTableColumn(
                'Datetime Added',
                'datetime_added',
                default_sort_direction='desc',
                default_sort=True),
            AttributeTableColumn(
                'Added By',
                'added_by.get_reversed_name',
                proxy_field='added_by.last_name'
            ),
            AttributeTableColumn('Problem', 'get_problem_str'),
            AttributeTableColumn('Description', 'description'),
            AttributeTableColumn('Confirmed?', 'is_validated'),
            ActionTableColumn(
                'Edit',
                actions=[
                    ActionItem(
                        'Edit Complaint',
                        GenesisTableLink(
                            'gdrives:edit-complaint',
                            url_args=[device.pk, GenesisTableLinkAttrArg('pk')]
                        )
                    ),
                    ActionItem(
                        'RMA Report',
                        GenesisTableLink(
                            'gdrives:rma-inspection-pdf',
                            url_args=[
                                device.pk, GenesisTableLinkAttrArg('pk')],
                            prefix=''
                        )
                    )
                ]
            )
        ]

    def get_above_table_items(self):
        device = self.get_device()
        return [
            GenesisAboveTableButton(
                'Add Complaint',
                reverse('gdrives:new-complaint', args=[device.pk])
            )
        ]

    def get_breadcrumbs(self):
        device = self.get_device()
        breadcrumbs = get_device_breadcrumbs(device, self.request.user)
        return breadcrumbs

    def get_page_title(self):
        return 'Complaints for {0}'.format(self.get_device().meid)

    def get_queryset(self):
        device = self.get_device()
        return device.complaints.all()
complaints = user_passes_test(admin_user)(GDriveComplaintTableView.as_view())


class NewGDriveComplaintFormView(GenesisFormView, GetDeviceMixin):
    form_class = GDriveComplaintForm
    success_message = 'The complaint has been added.'
    go_back_until = ['accounts:patient-communications']

    def _get_breadcrumbs(self):
        device = self.get_device()
        breadcrumbs = get_device_breadcrumbs(device, self.request.user)
        breadcrumbs.append(
            Breadcrumb('Complaints',
                       reverse('gdrives:complaints', args=[device.pk])))
        return breadcrumbs

    def get_form_kwargs(self):
        kwargs = super(NewGDriveComplaintFormView, self).get_form_kwargs()
        kwargs['requester'] = self.request.user
        kwargs['device'] = self.get_device()
        return kwargs

    def _get_page_title(self):
        device = self.get_device()
        return 'Add New Complaint for Device {0}'.format(device.meid)

    def get_success_url(self, form):
        return reverse('gdrives:complaints', args=[self.get_device().pk])
new_complaint = user_passes_test(admin_user)(
    NewGDriveComplaintFormView.as_view())


class EditGDriveComplaintFormView(GenesisFormView, GetDeviceMixin):
    form_class = RMAInspectionForm
    success_message = 'The complaint has been updated.'
    go_back_until = ['accounts:patient-communications']
    template_name = 'gdrives/edit_complaint.html'

    def _get_breadcrumbs(self):
        device = self.get_device()
        breadcrumbs = get_device_breadcrumbs(device, self.request.user)
        breadcrumbs.append(
            Breadcrumb('Complaints',
                       reverse('gdrives:complaints', args=[device.pk])))
        return breadcrumbs

    def get_complaint(self):
        if not hasattr(self, '_complaint'):
            device = self.get_device()
            self._complaint = device.complaints.get(
                pk=self.kwargs['complaint_id'])
        return self._complaint

    def get_context_data(self, **kwargs):
        kwargs['complaint'] = self.get_complaint()
        kwargs['updates'] = self.get_complaint().updates.order_by(
            'datetime_added')
        return super(EditGDriveComplaintFormView, self).get_context_data(
            **kwargs)

    def get_form_kwargs(self):
        kwargs = super(EditGDriveComplaintFormView, self).get_form_kwargs()
        kwargs['requester'] = self.request.user
        kwargs['instance'] = self.get_complaint()
        return kwargs

    def get_initial(self):
        return {'rma_return_date': now().date()}

    def _get_page_title(self):
        device = self.get_device()
        return 'Edit Complaint for Device {0}'.format(device.meid)

    def get_success_url(self, form):
        return reverse('gdrives:complaints', args=[self.get_device().pk])
edit_complaint = user_passes_test(admin_user)(
    EditGDriveComplaintFormView.as_view())


class RMAInspectionReportView(ReportView, GetDeviceMixin):
    template_name = 'gdrives/reports/rma_inspection.html'
    filename = 'rma_inspection.pdf'
    response_class = PDFPrintURLResponse

    def get_complaint(self):
        if not hasattr(self, '_complaint'):
            self._complaint = self.get_device().complaints.get(
                pk=self.kwargs['complaint_id'])
        return self._complaint

    def get_context_data(self, **kwargs):
        return {
            'complaint': self.get_complaint()
        }
rma_inspection_pdf = user_passes_test(admin_user)(
    RMAInspectionReportView.as_view(output_format='pdf'))
rma_inspection_pdf_html = user_passes_test(admin_user)(
    RMAInspectionReportView.as_view(output_format='html'))


class RMASummaryConfigureView(GenesisFormView):
    form_class = RMASummaryConfigureForm
    page_title = 'Configure RMA Meter Testing Determination Report'
    success_message = 'Your report has been generated.'
    form_message = (
        "This report is based on the date the meter was returned to GHT not "
        "the original complaint date.")

    def get_success_url(self, form):
        dt_format = "%Y/%m/%d"
        date_info = {
            'start_date': form.cleaned_data['start_date'].strftime(dt_format),
            'end_date': form.cleaned_data['end_date'].strftime(dt_format)
        }
        return "{0}?{1}".format(
            reverse('gdrives:rma-summary-report'),
            urlencode(date_info)
        )
configure_rma_summary_report = user_passes_test(admin_user)(
    RMASummaryConfigureView.as_view())


class RMASummaryReportView(ReportView):
    template_name = 'gdrives/reports/rma_summary.html'
    filename = 'rma summary.pdf'
    response_class = PDFPrintURLResponse

    def get_context_data(self):
        start_date, end_date = self.get_timeframe()
        qs = GDriveComplaint.objects.filter(
            rma_return_date__range=(start_date, end_date))
        categories = map(
            lambda x: x['name'],
            DeviceProblem.objects.values('name'))
        final_categories = []
        customer_data = []
        confirmed_data = []
        inspector_found_data = []
        for cat_ in categories:
            customer_count = qs.filter(reported_problems__name=cat_).count()
            confirmed_count = qs.filter(reported_problems__name=cat_,
                                        is_validated=True).count()
            inspector_count = qs.filter(
                found_problems__name=cat_).count()
            if customer_count == 0 and inspector_count == 0:
                continue
            final_categories.append(cat_)
            customer_data.append(customer_count)
            confirmed_data.append(confirmed_count)
            inspector_found_data.append(inspector_count)
        customer_found_series = {
            'name': 'Original Complaints: {0}'.format(sum(customer_data)),
            'data': customer_data
        }
        confirmed_series = {
            'name': 'Confirmed Complaints: {0}'.format(sum(confirmed_data)),
            'data': confirmed_data
        }
        inspector_found_series = {
            'name': 'Inspector Findings: {0}'.format(
                sum(inspector_found_data)),
            'data': inspector_found_data
        }
        series = [
            customer_found_series,
            confirmed_series,
            inspector_found_series
        ]
        date_format = "%b %Y"
        chart_title = 'Returned Meter Testing Determination {0} - {1}'.format(
            start_date.strftime(date_format), end_date.strftime(date_format))
        return {
            'categories': final_categories,
            'series': series,
            'chart_title': chart_title,
            'querystring': urlencode({
                'start_date': start_date.strftime("%Y/%m/%d"),
                'end_date': end_date.strftime("%Y/%m/%d")
            })
        }

    def get_timeframe(self):
        default_start_date = now() - relativedelta(months=3)
        if 'start_date' in self.request.GET:
            start_date = parse(self.request.GET['start_date'])
        else:
            start_date = default_start_date
        if 'end_date' in self.request.GET:
            end_date = parse(self.request.GET['end_date'])
        else:
            end_date = start_date + relativedelta(months=4)
        return start_date, end_date
rma_summary_report = user_passes_test(admin_user)(
    RMASummaryReportView.as_view())
rma_summary_report_print = user_passes_test(admin_user)(
    RMASummaryReportView.as_view(
        template_name='gdrives/reports/rma_summary_print.html'))
rma_summary_report_pdf = user_passes_test(admin_user)(
    RMASummaryReportView.as_view(
        template_name='gdrives/reports/rma_summary_pdf.html',
        output_format='pdf'))
