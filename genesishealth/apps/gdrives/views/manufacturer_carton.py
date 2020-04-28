from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse

from genesishealth.apps.gdrives.models import GDrive, GDriveManufacturerCarton
from genesishealth.apps.gdrives.forms import (
    GDriveManufacturerCartonForm, InspectManufacturerCartonForm,
    ManufacturerCartonImportForm)
from genesishealth.apps.reports.views.main import (
    ReportView, PDFPrintURLResponse)
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.class_views import (
    ActionItem, ActionTableColumn, AttributeTableColumn,
    GenesisAboveTableButton, GenesisFormMixin, GenesisFormView,
    GenesisTableLink, GenesisTableLinkAttrArg, GenesisTableView)
from genesishealth.apps.utils.request import admin_user


class ManufacturerCartonImportFormView(GenesisFormView):
    form_class = ManufacturerCartonImportForm
    success_message = 'The cartons have been added.'
    page_title = 'Import Manufacturer Cartons'

    def get_breadcrumbs(self):
        return [
            Breadcrumb(
                'Manufacturer Cartons',
                reverse('gdrives:manufacturer-cartons'))
        ]

    def get_success_url(self, form):
        return reverse('gdrives:manufacturer-cartons')


import_manufacturer_carton_csv = user_passes_test(admin_user)(
    ManufacturerCartonImportFormView.as_view())


class ManufacturerCartonTableView(GenesisTableView):
    def create_columns(self):
        return [
            AttributeTableColumn('Carton Number', 'number'),
            AttributeTableColumn('Lot Number', 'lot_number'),
            AttributeTableColumn('Date Shipped', 'date_shipped'),
            ActionTableColumn(
                'Actions',
                actions=[
                    ActionItem(
                        'Inspect',
                        GenesisTableLink(
                            'gdrives:inspect-manufacturer-carton',
                            url_args=[GenesisTableLinkAttrArg('pk')]),
                        condition=['!is_inspected']
                    ),
                    ActionItem(
                        'Inspection Report',
                        GenesisTableLink(
                            'gdrives:manufacturer-carton-pdf',
                            url_args=[GenesisTableLinkAttrArg('pk')],
                            prefix=''
                        ),
                        condition=['is_inspected']
                    ),
                    ActionItem(
                        'Edit',
                        GenesisTableLink(
                            'gdrives:edit-manufacturer-carton',
                            url_args=[GenesisTableLinkAttrArg('pk')])
                    )
                ]
            )
        ]

    def get_above_table_items(self):
        return [
            GenesisAboveTableButton(
                'Add Manufacturer Carton',
                reverse('gdrives:add-manufacturer-carton')
            ),
            GenesisAboveTableButton(
                'Import Manufacturer Cartons',
                reverse('gdrives:import-manufacturer-cartons')
            )
        ]

    def get_page_title(self):
        return 'Manage Manufacturer Cartons'

    def get_queryset(self):
        return GDriveManufacturerCarton.objects.all()
manufacturer_cartons = user_passes_test(admin_user)(
    ManufacturerCartonTableView.as_view())


class NewGDriveManufacturerCartonFormView(GenesisFormView):
    form_class = GDriveManufacturerCartonForm
    page_title = 'Add Manufacturer Carton'
    success_message = 'The manufacturer carton has been added.'

    def get_breadcrumbs(self):
        return [
            Breadcrumb('Manufacturer Cartons',
                       reverse('gdrives:manufacturer-cartons'))
        ]

    def get_success_url(self, form):
        return reverse('gdrives:manufacturer-cartons')
new_manufacturer_carton = user_passes_test(admin_user)(
    NewGDriveManufacturerCartonFormView.as_view())


class EditGDriveManufacturerCartonFormView(GenesisFormView):
    form_class = GDriveManufacturerCartonForm
    success_message = 'The manufacturer carton has been updated.'

    def get_breadcrumbs(self):
        return [
            Breadcrumb('Manufacturer Cartons',
                       reverse('gdrives:manufacturer-cartons'))
        ]

    def get_carton(self):
        if not hasattr(self, '_carton'):
            self._carton = GDriveManufacturerCarton.objects.get(
                pk=self.kwargs['carton_id'])
        return self._carton

    def get_form_kwargs(self):
        kwargs = super(EditGDriveManufacturerCartonFormView, self)\
            .get_form_kwargs()
        kwargs['instance'] = self.get_carton()
        return kwargs

    def get_page_title(self):
        return 'Edit Manufacturer Carton {0}'.format(
            self.get_carton().number)

    def get_success_url(self, form):
        return reverse('gdrives:manufacturer-cartons')
edit_manufacturer_carton = user_passes_test(admin_user)(
    EditGDriveManufacturerCartonFormView.as_view())


class InspectManfacturerCartonView(GenesisTableView, GenesisFormMixin):
    form_class = InspectManufacturerCartonForm
    success_message = 'The carton has been inspected.'
    template_name = 'gdrives/inspect_manufacturer_carton.html'

    def create_columns(self):
        return [
            AttributeTableColumn('MEID', 'meid'),
            AttributeTableColumn('Serial #', 'device_id'),
            AttributeTableColumn('Tray #', 'tray_number'),
            AttributeTableColumn('Non-Conformity', 'get_non_conformity_str')
        ]

    def get_breadcrumbs(self):
        return [
            Breadcrumb('Manufacturer Cartons',
                       reverse('gdrives:manufacturer-cartons'))
        ]

    def get_carton(self):
        if not hasattr(self, '_carton'):
            self._carton = GDriveManufacturerCarton.objects.get(
                id=self.kwargs['carton_id'])
        return self._carton

    def get_context_data(self, **kwargs):
        if 'form' not in kwargs:
            kwargs['form'] = self.get_form()
        kwargs['carton'] = self.get_carton()
        return super(InspectManfacturerCartonView, self).get_context_data(
            **kwargs)

    def get_form_kwargs(self):
        kwargs = super(InspectManfacturerCartonView, self).get_form_kwargs()
        kwargs['requester'] = self.request.user
        kwargs['carton'] = self.get_carton()
        return kwargs

    def get_page_title(self):
        return 'Inspect Manufacturer Carton {0}'.format(
            self.get_carton().number)

    def get_queryset(self):
        return self.get_carton().devices.filter(
            status=GDrive.DEVICE_STATUS_REPAIRABLE)

    def get_success_url(self, form):
        return reverse('gdrives:manufacturer-cartons')

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
inspect_manufacturer_carton = user_passes_test(admin_user)(
    InspectManfacturerCartonView.as_view())


class ManufacturerCartonInspectionReportView(ReportView):
    template_name = 'gdrives/reports/manu_carton_inspection.html'
    filename = 'carton.pdf'
    response_class = PDFPrintURLResponse

    def get_carton(self):
        if not hasattr(self, '_carton'):
            self._carton = GDriveManufacturerCarton.objects.get(
                pk=self.kwargs['carton_id'])
        return self._carton

    def get_context_data(self, **kwargs):
        return {
            'devices': self.get_carton().devices.all(),
            'carton': self.get_carton()
        }
manufacturer_carton_inspection_pdf = \
    user_passes_test(admin_user)(
        ManufacturerCartonInspectionReportView.as_view(
            output_format='pdf'))
manufacturer_carton_inspection_pdf_html = \
    user_passes_test(admin_user)(
        ManufacturerCartonInspectionReportView.as_view(
            output_format='html'))
