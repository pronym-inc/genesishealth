from django import forms
from django.urls import reverse

from genesishealth.apps.gdrives.models import GDrive, GDriveWarehouseCarton
from genesishealth.apps.orders.models import (
    Order, OrderShipment, ShippingClass, ShippingPackageType)
from genesishealth.apps.utils.class_views import GenesisFormView
from genesishealth.apps.utils.forms import GenesisForm
from genesishealth.apps.utils.request import require_admin_permission
from genesishealth.apps.utils.widgets import (
    AdditionalModelMultipleChoiceWidget)


test = require_admin_permission('orders')


class CreateShipmentForm(GenesisForm):
    meid = forms.CharField(label="MEID", required=False)
    package_type = forms.ModelChoiceField(
        queryset=ShippingPackageType.objects.filter(enabled=True))
    warehouse_cartons = forms.ModelMultipleChoiceField(
        queryset=None,
        to_field_name='number',
        required=False,
        widget=AdditionalModelMultipleChoiceWidget)
    shipping_class = forms.ModelChoiceField(
        queryset=ShippingClass.objects.filter(is_for_bulk=True))
    weight_pounds = forms.IntegerField()
    weight_ounces = forms.FloatField()

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order')
        self.requester = kwargs.pop('requester')
        self.rx_partner = kwargs.pop('rx_partner', None)
        super(CreateShipmentForm, self).__init__(*args, **kwargs)
        if not self.should_have_meid():
            del self.fields['meid']
        if self.order.is_patient_order():
            del self.fields['warehouse_cartons']
            del self.fields['shipping_class']
        else:
            self.fields['warehouse_cartons'].queryset = \
                GDriveWarehouseCarton.objects.filter(
                    rx_partner=self.rx_partner,
                    is_shipped=False)
            del self.fields['weight_pounds']
            del self.fields['weight_ounces']

    def clean(self):
        data = super(CreateShipmentForm, self).clean()
        if self.should_have_meid():
            try:
                assert 'meid' in data
                GDrive.objects.get(
                    meid=data['meid'],
                    status=GDrive.DEVICE_STATUS_AVAILABLE)
            except (AssertionError, GDrive.DoesNotExist):
                raise forms.ValidationError(
                    "The ID provided for device {0} did not match an "
                    "available device.".format(data['meid']))
        elif not self.order.is_patient_order():
            carton_numbers = data.get('warehouse_cartons', [])
            # Figure out how many cartons we expect, then make
            # sure that's how many they've chosen.
            expected_cartons = sum(
                [entry.quantity for entry in self.order.entries.filter(
                    product__is_device=True)])
            if len(carton_numbers) != expected_cartons:
                raise forms.ValidationError(
                    "You must provide {0} cartons.  You provided {1}."
                    .format(expected_cartons, len(carton_numbers)))
        return data

    def save(self):
        data = self.cleaned_data
        shipment_kwargs = {
            'order': self.order,
            'package_type': data['package_type'],
            'packed_by': self.requester
        }
        if self.order.is_patient_order():
            shipment_kwargs['weight_pounds'] = data['weight_pounds']
            shipment_kwargs['weight_ounces'] = data['weight_ounces']
        shipment = OrderShipment.objects.create(**shipment_kwargs)
        if self.should_have_meid():
            device = GDrive.objects.get(
                meid=data['meid'],
                status=GDrive.DEVICE_STATUS_AVAILABLE)
            device.shipment = shipment
            device.save()
            self.order.patient.patient_profile.replace_device(device)
        elif not self.order.is_patient_order():
            for warehouse_carton in data['warehouse_cartons']:
                warehouse_carton.assign_to_shipment(shipment)
            # We don't do an extra finalize step for bulk orders,
            # since we aren't going through the Stamps API
            shipment.shipping_class = data['shipping_class']
            shipment.is_finalized = True
            shipment.save()
        self.instance = shipment
        return shipment

    def should_have_meid(self):
        return (
            self.order.is_patient_order() and
            self.order.entries.filter(product__is_device=True).count() > 0)


class CreateShipmentView(GenesisFormView):
    form_class = CreateShipmentForm
    go_back_until = ['orders:worklist']
    template_name = "orders/create_shipment.html"

    def get_context_data(self, **kwargs):
        ctx = super(CreateShipmentView, self).get_context_data(**kwargs)
        ctx['order'] = self.get_order()
        return ctx

    def get_form_kwargs(self):
        kwargs = super(CreateShipmentView, self).get_form_kwargs()
        order = self.get_order()
        kwargs['order'] = order
        kwargs['requester'] = self.request.user
        if not order.is_patient_order():
            kwargs['rx_partner'] = order.rx_partner
        return kwargs

    def get_order(self):
        if not hasattr(self, '_order'):
            self._order = Order.objects.get(pk=self.kwargs['order_id'])
        return self._order

    def get_page_title(self):
        order = self.get_order()
        if order.patient:
            for_label = order.patient.get_reversed_name()
        else:
            for_label = order.rx_partner.name
        return "Create Shipment for Order #{0} for {1}".format(
            order.id, for_label)

    def get_success_message(self, form):
        if self.get_order().is_patient_order():
            return "The shipment is ready to be finalized."
        return "The shipment has been created."

    def get_success_url(self, form):
        order = self.get_order()
        if order.is_patient_order():
            return reverse('orders:finalize-shipment', args=[form.instance.pk])
        # Take them to shipment edit screen so they can enter in the
        # tracking #
        return reverse('orders:edit-shipment', args=[form.instance.pk])


main = test(CreateShipmentView.as_view())
