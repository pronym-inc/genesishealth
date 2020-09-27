from django import forms
from django.urls import reverse

from genesishealth.apps.orders.form_fields import (
    SelectProductsField, SelectProductsWidget)
from genesishealth.apps.orders.models import Order
from genesishealth.apps.pharmacy.models import PharmacyPartner
from genesishealth.apps.pharmacy.breadcrumbs import get_rx_partner_breadcrumbs
from genesishealth.apps.utils.class_views import GenesisFormView
from genesishealth.apps.utils.forms import GenesisForm
from genesishealth.apps.utils.request import require_admin_permission


test = require_admin_permission('pharmacy')


product_error_messages = {'required': 'You must choose a product.'}


class CreateRxBulkOrderForm(GenesisForm):
    products = SelectProductsField(
        error_messages=product_error_messages, required=False,
        widget=SelectProductsWidget(is_bulk=True))
    invoice_number = forms.CharField()

    def __init__(self, *args, **kwargs):
        self._rx_partner = kwargs.pop('rx_partner')
        super(CreateRxBulkOrderForm, self).__init__(*args, **kwargs)

    def clean(self):
        errors = []
        if not self.cleaned_data['products']:
            errors.append("You must choose at least one product.")
        if errors:
            msg = "\n".join(errors)
            raise forms.ValidationError(msg)
        return self.cleaned_data

    def save(self, commit=True):
        order = Order.objects.create(
            rx_partner=self._rx_partner,
            invoice_number=self.cleaned_data['invoice_number'],
            order_type=Order.ORDER_TYPE_BULK,
            order_origin=Order.ORDER_ORIGIN_BULK_ORDER
        )
        for entry in self.cleaned_data['products']:
            entry.order = order
            entry.save()
        self.instance = order
        return order


class CreateRxBulkOrderView(GenesisFormView):
    form_class = CreateRxBulkOrderForm
    go_back_until = ['pharmacy:details']
    success_message = "The bulk order has been created."

    def _get_breadcrumbs(self):
        return get_rx_partner_breadcrumbs(
            self.get_rx_partner(), self.request.user)

    def get_form_kwargs(self):
        kwargs = super(CreateRxBulkOrderView, self).get_form_kwargs()
        kwargs['rx_partner'] = self.get_rx_partner()
        return kwargs

    def _get_page_title(self):
        return "Create Bulk Order for {0}".format(self.get_rx_partner())

    def get_rx_partner(self):
        if not hasattr(self, '_rx_partner'):
            self._rx_partner = PharmacyPartner.objects.get(
                pk=self.kwargs['rx_partner_id'])
        return self._rx_partner

    def get_success_url(self, form):
        return reverse('orders:details', args=[form.instance.pk])


main = test(CreateRxBulkOrderView.as_view())
