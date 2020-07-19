from django import forms
from django.urls import reverse

from genesishealth.apps.accounts.breadcrumbs.patients import (
    get_patient_breadcrumbs)
from genesishealth.apps.orders.models import OrderShipment
from genesishealth.apps.pharmacy.breadcrumbs import get_rx_partner_breadcrumbs
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.class_views import GenesisFormView
from genesishealth.apps.utils.forms import GenesisModelForm
from genesishealth.apps.utils.request import require_admin_permission


test = require_admin_permission('orders')


class EditShipmentForm(GenesisModelForm):
    class Meta:
        model = OrderShipment
        fields = ('tracking_number',)

    def clean_tracking_number(self):
        tracking_number = self.cleaned_data['tracking_number']
        qs = OrderShipment.objects.all()
        if self.instance.pk is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.filter(tracking_number=tracking_number).count() > 0:
            raise forms.ValidationError(
                "That tracking number is already in use.")
        return tracking_number


class EditShipmentView(GenesisFormView):
    form_class = EditShipmentForm
    go_back_until = ['orders:shipments']
    success_message = "The shipment has been updated."

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
        kwargs = super(EditShipmentView, self).get_form_kwargs()
        kwargs['instance'] = self.get_shipment()
        return kwargs

    def get_shipment(self):
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
        return "Edit Shipment for Order #{0} for {1}".format(
            order.id, for_label)

    def get_success_url(self, form):
        return reverse('orders:details', args=[form.instance.order.pk])


main = test(EditShipmentView.as_view())
