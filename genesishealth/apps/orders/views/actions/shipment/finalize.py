from django import forms
from django.urls import reverse

from genesishealth.apps.accounts.breadcrumbs.patients import (
    get_patient_breadcrumbs)
from genesishealth.apps.orders.models import OrderShipment, ShippingClass
from genesishealth.apps.pharmacy.breadcrumbs import get_rx_partner_breadcrumbs
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.class_views import GenesisFormView
from genesishealth.apps.utils.forms import GenesisModelForm
from genesishealth.apps.utils.request import require_admin_permission


test = require_admin_permission('orders')


class ShippingClassField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        if obj.stamps_abbreviation in self._rates:
            rate = "${0}".format(self._rates[obj.stamps_abbreviation])
        else:  # pragma: no cover
            rate = "N/A"
        return "{0} ({1})".format(obj.name, rate)

    def set_rates(self, rates):
        self._rates = rates


class FinalizeShipmentForm(GenesisModelForm):
    shipping_class = ShippingClassField(queryset=None)

    class Meta:
        model = OrderShipment
        fields = ('shipping_class',)

    def __init__(self, *args, **kwargs):
        self.rates = kwargs.pop('rates')
        super(FinalizeShipmentForm, self).__init__(*args, **kwargs)
        self.fields['shipping_class'].set_rates(self.rates)
        self.fields['shipping_class'].queryset = ShippingClass.objects.filter(
            stamps_abbreviation__in=self.rates.keys(),
            enabled=True)


class FinalizeShipmentView(GenesisFormView):
    form_class = FinalizeShipmentForm
    go_back_until = ['orders:worklist', 'orders:shipments']
    success_message = "The order has been marked shipped."

    def form_valid(self, form):
        self.get_shipment().finalize(self.request.user)
        return super(FinalizeShipmentView, self).form_valid(form)

    def _get_breadcrumbs(self):
        order = self.get_shipment().order
        if order.is_patient_order():
            patient = order.patient
            breadcrumbs = get_patient_breadcrumbs(patient, self.request.user)
            breadcrumbs.append(
                Breadcrumb(
                    'Orders',
                    reverse('accounts:patient-orders', args=[patient.pk]))
            )
        else:
            rx_partner = order.rx_partner
            breadcrumbs = get_rx_partner_breadcrumbs(
                rx_partner, self.request.user)
        return breadcrumbs

    def get_form_kwargs(self):
        kwargs = super(FinalizeShipmentView, self).get_form_kwargs()
        shipment = self.get_shipment()
        kwargs['instance'] = shipment
        rates = shipment.get_shipping_rates(get_all=True)
        rate_info = {r.service_type.value: r.amount for r in rates}
        kwargs['rates'] = rate_info
        return kwargs

    def get_shipment(self) -> OrderShipment:
        if not hasattr(self, '_shipment'):
            self._shipment = OrderShipment.objects.get(
                pk=self.kwargs['shipment_id'])
        return self._shipment

    def _get_page_title(self):
        order = self.get_shipment().order
        if order.patient:
            for_label = order.patient.get_reversed_name()
        else:
            for_label = order.rx_partner.name
        return "Finalize Shipment for Order #{0} for {1}".format(
            order.id, for_label)

    def get_success_url(self, form):
        return reverse('orders:details', args=[form.instance.order.pk])


main = test(FinalizeShipmentView.as_view())
