from django import forms

from genesishealth.apps.orders.models import Order
from genesishealth.apps.pharmacy.models import PharmacyPartner
from genesishealth.apps.utils.class_views import GenesisFormView
from genesishealth.apps.utils.forms import GenesisForm
from genesishealth.apps.utils.func import read_csv_file
from genesishealth.apps.utils.request import require_admin_permission


test = require_admin_permission('pharmacy')


class FulfillOrdersForm(GenesisForm):
    csv = forms.FileField(label="Fulfillment Import File")

    CSV_FIELD_NAMES = ('order_id', 'success')

    def clean_csv(self):
        data = read_csv_file(self.cleaned_data['csv'], self.CSV_FIELD_NAMES)
        self.successful_orders = []
        errors = []
        for idx, row in enumerate(data):
            try:
                order = Order.objects.get(pk=row['order_id'])
            except Order.DoesNotExist:
                errors.append("Row {0}: Invalid order id {1}".format(
                    idx, row['order_id']))
                continue
            if not order.can_be_fulfilled():
                errors.append(
                    "Row {0}: Invalid order {1} - order cannot be fulfilled.")
            if errors:
                continue
            if row['success'].lower() == 'y':
                self.successful_orders.append(order)
        if errors:
            raise forms.ValidationError("\n".join(errors))
        return self.cleaned_data['csv']


class FulfillOrdersView(GenesisFormView):
    form_class = FulfillOrdersForm
    go_back_until = ['pharmacy:index']
    success_message = "The orders have been updated."

    def form_valid(self, form):
        for order in form.successful_orders:
            order.fulfill()
        return super(FulfillOrdersView, self).form_valid(form)

    def _get_page_title(self):
        return "Fulfill Orders for Rx Partner {0}".format(
            self.get_rx_partner().name)

    def get_rx_partner(self):
        if not hasattr(self, '_rx_partner'):
            self._rx_partner = PharmacyPartner.objects.get(
                id=self.kwargs['rx_partner_id'])
        return self._rx_partner


main = test(FulfillOrdersView.as_view())
