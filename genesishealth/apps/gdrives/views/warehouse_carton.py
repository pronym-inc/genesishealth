from django import forms
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse
from django.http import HttpResponse
from django.utils.timezone import localtime
from django.views.generic import TemplateView

from genesishealth.apps.gdrives.forms import (
    AddGDriveToWarehouseCartonForm, CreateWarehouseCartonForm)
from genesishealth.apps.gdrives.models import GDrive, GDriveWarehouseCarton
from genesishealth.apps.pharmacy.models import PharmacyPartner
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.class_views import (
    AttributeTableColumn, GenesisAboveTableButton, GenesisAboveTableDropdown,
    GenesisDropdownOption, GenesisFormView, GenesisTableView)
from genesishealth.apps.utils.class_views.form import GenesisBatchFormView
from genesishealth.apps.utils.forms import GenesisBatchForm, GenesisForm
from genesishealth.apps.utils.request import admin_user


class WarehouseCartonTableView(GenesisTableView):
    def create_columns(self):
        return [
            AttributeTableColumn(
                'Date/Time Added',
                'datetime_added',
                default_sort=True,
                default_sort_direction='desc'),
            AttributeTableColumn("Is Shipped?", 'is_shipped'),
            AttributeTableColumn('Carton Number', 'number'),
            AttributeTableColumn('Rx Partner', 'rx_partner.name'),
            AttributeTableColumn('# Devices', 'get_device_count')
        ]

    def get_above_table_items(self):
        return [
            GenesisAboveTableButton(
                'Add Warehouse Carton',
                reverse('gdrives:add-warehouse-carton')
            ),
            GenesisAboveTableButton(
                'Generate Barcodes',
                reverse('gdrives:generate-warehouse-carton-labels')),
            GenesisAboveTableDropdown(
                [GenesisDropdownOption(
                    'Assign to Partner',
                    reverse('gdrives:batch-assign-carton-to-rx'))]
            )
        ]

    def get_page_title(self):
        return 'Manage Warehouse Cartons'

    def get_queryset(self):
        return GDriveWarehouseCarton.objects.all()
warehouse_cartons = user_passes_test(admin_user)(
    WarehouseCartonTableView.as_view())


class AddWarehouseCartonView(GenesisTableView):
    template_name = 'gdrives/new_warehouse_carton.html'

    def create_columns(self):
        return [
            AttributeTableColumn('MEID', 'meid'),
            AttributeTableColumn('Serial #', 'device_id'),
            AttributeTableColumn('Lot #', 'manufacturer_carton.lot_number'),
        ]

    def get(self, request, *args, **kwargs):
        if request.GET.get('ajax', None) is None:
            self.request.session['new_warehouse_device_ids'] = []
        return super(AddWarehouseCartonView, self).get(
            request, *args, **kwargs)

    def get_cached_devices(self):
        try:
            pks = self.request.session['new_warehouse_device_ids']
        except KeyError:
            return GDrive.objects.none()
        return GDrive.objects.filter(
            status=GDrive.DEVICE_STATUS_AVAILABLE).filter(pk__in=pks)

    def get_context_data(self, **kwargs):
        kwargs['form'] = AddGDriveToWarehouseCartonForm()
        kwargs['finish_form'] = CreateWarehouseCartonForm()
        return super(AddWarehouseCartonView, self).get_context_data(**kwargs)

    def get_page_title(self):
        return 'Add Warehouse Carton'

    def get_queryset(self):
        return self.get_cached_devices()

    def post(self, request, *args, **kwargs):
        if request.POST.get('device', None) is not None:
            form = AddGDriveToWarehouseCartonForm(
                {'device': request.POST['device']})
            if len(self.request.session['new_warehouse_device_ids']) >= 30:
                return HttpResponse('Carton Full', status=400)
            if not form.is_valid():
                return HttpResponse('Invalid MEID', status=400)
            if form.cleaned_data['device'].pk in self.request.session[
                    'new_warehouse_device_ids']:
                return HttpResponse('Duplicate MEID', status=400)
            self.request.session['new_warehouse_device_ids'].append(
                form.cleaned_data['device'].pk)
            self.request.session.save()
            return HttpResponse()
        return HttpResponse(status=404)
add_warehouse_carton = user_passes_test(admin_user)(
    AddWarehouseCartonView.as_view())


class FinishWarehouseCartonFormView(GenesisFormView):
    form_class = CreateWarehouseCartonForm
    success_message = 'The warehouse carton has been added.'

    def get_form_kwargs(self):
        kwargs = super(FinishWarehouseCartonFormView, self).get_form_kwargs()
        kwargs['devices'] = GDrive.objects.filter(
            status=GDrive.DEVICE_STATUS_AVAILABLE).filter(
            pk__in=self.request.session['new_warehouse_device_ids'])
        return kwargs

    def get_page_title(self):
        return 'Finish Warehouse Carton'

    def get_success_url(self, form):
        return reverse('gdrives:warehouse-cartons')
finish_warehouse_carton = user_passes_test(admin_user)(
    FinishWarehouseCartonFormView.as_view())


class BatchAssignToRxPartnerForm(GenesisBatchForm):
    rx_partner = forms.ModelChoiceField(queryset=PharmacyPartner.objects.all())

    def save(self):
        for warehouse_carton in self.batch:
            warehouse_carton.rx_partner = self.cleaned_data['rx_partner']
            warehouse_carton.save()


class BatchAssignToRxPartnerFormView(GenesisBatchFormView):
    form_class = BatchAssignToRxPartnerForm
    page_title = "Assign Warehouse Cartons to Rx Partner"
    success_message = "The warehouse cartons have been successfully assigned"

    def get_batch_queryset(self):
        return GDriveWarehouseCarton.objects.all()
batch_assign_carton_to_rx = user_passes_test(admin_user)(
    BatchAssignToRxPartnerFormView.as_view())


class GenerateWarehouseCartonLabelsForm(GenesisForm):
    quantity = forms.IntegerField(min_value=1, max_value=1000)


class GenerateWarehouseCartonLabelsView(GenesisFormView):
    page_title = "Generate Warehouse Carton Labels"
    form_class = GenerateWarehouseCartonLabelsForm
    success_message = "Your labels have been generated."
    do_raw_redirect = True

    def get_breadcrumbs(self):
        return [
            Breadcrumb(
                'Warehouse Cartons', reverse('gdrives:warehouse-cartons'))
        ]

    def get_success_url(self, form):
        return "{0}?quantity={1}".format(
            reverse('gdrives:warehouse-carton-labels'),
            form.cleaned_data['quantity'])
generate_warehouse_carton_labels = user_passes_test(admin_user)(
    GenerateWarehouseCartonLabelsView.as_view())


class WarehouseCartonLabelsView(TemplateView):
    template_name = "gdrives/warehouse_carton_labels.html"

    def generate_new_barcodes(self, quantity):
        barcodes = []
        base = localtime().strftime("%Y%m%dD")
        counter = 0
        while len(barcodes) < quantity:
            counter += 1
            new_barcode = base + str(counter).zfill(5)
            try:
                GDriveWarehouseCarton.objects.get(number=new_barcode)
            except GDriveWarehouseCarton.DoesNotExist:
                barcodes.append(new_barcode)
        return barcodes

    def get_context_data(self, **kwargs):
        data = TemplateView.get_context_data(self, **kwargs)
        data['barcodes'] = self.generate_new_barcodes(
            int(self.request.GET['quantity']))
        return data
warehouse_carton_labels = user_passes_test(admin_user)(
    WarehouseCartonLabelsView.as_view())
