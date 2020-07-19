from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse

from genesishealth.apps.dropdowns.models import MeterDisposition
from genesishealth.apps.gdrives.breadcrumbs import get_device_breadcrumbs
from genesishealth.apps.gdrives.forms import GDriveNonConformityForm
from genesishealth.apps.gdrives.models import GDrive
from genesishealth.apps.gdrives.views.base import GetDeviceMixin
from genesishealth.apps.reports.views.main import (
    ReportView, PDFPrintURLResponse)
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.class_views import (
    AttributeTableColumn, GenesisAboveTableButton, GenesisFormView,
    GenesisTableView)
from genesishealth.apps.utils.request import admin_user


class GDriveNonConformityTableView(GenesisTableView, GetDeviceMixin):
    def create_columns(self):
        return [
            AttributeTableColumn(
                'Datetime Added',
                'datetime_added',
                default_sort_direction='desc',
                default_sort=True
            ),
            AttributeTableColumn(
                'Added By',
                'added_by.get_reversed_name',
                proxy_field='added_by.last_name'),
            AttributeTableColumn('Type', 'non_conformity_type.name'),
            AttributeTableColumn('Description', 'description')
        ]

    def get_above_table_items(self):
        device = self.get_device()
        return [
            GenesisAboveTableButton(
                'Add Non-Conformity',
                reverse('gdrives:new-non-conformity', args=[device.pk])
            )
        ]

    def get_breadcrumbs(self):
        device = self.get_device()
        breadcrumbs = get_device_breadcrumbs(device, self.request.user)
        return breadcrumbs

    def get_page_title(self):
        return 'Non-Conformity Records for {0}'.format(self.get_device().meid)

    def get_queryset(self):
        return self.get_device().non_conformities.all()
non_conformities = user_passes_test(admin_user)(
    GDriveNonConformityTableView.as_view())


class GDriveNewNonConformityFormView(GenesisFormView, GetDeviceMixin):
    form_class = GDriveNonConformityForm
    go_back_until = ['gdrives:non-conformities']
    success_message = 'The non-conformity has been added.'

    def _get_breadcrumbs(self):
        device = self.get_device()
        breadcrumbs = get_device_breadcrumbs(
            device, self.request.user)
        breadcrumbs.append(
            Breadcrumb('Non-Conformities',
                       reverse('gdrives:non-conformities',
                               args=[device.pk])))
        return breadcrumbs

    def get_form_kwargs(self):
        kwargs = super(GDriveNewNonConformityFormView, self).get_form_kwargs()
        kwargs['requester'] = self.request.user
        kwargs['device'] = self.get_device()
        return kwargs
new_non_conformity = user_passes_test(admin_user)(
    GDriveNewNonConformityFormView.as_view())


class GDriveNonConformityReportView(ReportView):
    template_name = 'gdrives/reports/non_conformity.html'
    filename = 'nonconformity.pdf'
    response_class = PDFPrintURLResponse

    def get_context_data(self, **kwargs):
        device = GDrive.objects.get(pk=self.kwargs['device_id'])
        non_conformity = device.non_conformities.all()[0]
        # We need date-sorted list of rework records AND inspection
        # records, combined.  Make a list of generic dictionaries to handle
        # the different data types.
        rework_inspect_records = []
        for rw_rec in device.rework_records.all():
            rework_inspect_records.append({
                'disposition': rw_rec.new_disposition.name,
                'posted_datetime': rw_rec.datetime_reworked,
                'author': rw_rec.reworked_by,
                'is_ready_for_inspection': rw_rec.ready_for_inspection,
                'details': rw_rec.details,
                'is_inspection': False
            })

        available_dis = MeterDisposition.objects.filter(is_problem=False)
        if available_dis.count() > 0:
            available_name = available_dis[0].name
        else:
            available_name = "Available for Delivery"
        for inspec_rec in device.inspection_records.all():
            rework_inspect_records.append({
                'disposition': available_name,
                'posted_datetime': inspec_rec.datetime_inspected,
                'author': inspec_rec.inspected_by,
                'is_ready_for_inspection': 'SKIP',
                'details': None,
                'is_inspection': True
            })
        # Sort by date.
        rework_inspect_records = sorted(
            rework_inspect_records,
            key=lambda x: x['posted_datetime'])
        return {
            'non_conformity': non_conformity,
            'device': non_conformity.device,
            'records': rework_inspect_records
        }

non_conformity_report = user_passes_test(admin_user)(
    GDriveNonConformityReportView.as_view())
non_conformity_report_print = user_passes_test(admin_user)(
    GDriveNonConformityReportView.as_view(
        template_name='gdrives/reports/non_conformity_print.html'))
non_conformity_report_pdf = user_passes_test(admin_user)(
    GDriveNonConformityReportView.as_view(
        template_name='gdrives/reports/non_conformity_print.html',
        output_format='pdf'))
