from django import forms
from django.contrib.auth.models import User

from genesishealth.apps.orders.models import Order, OrderEntry
from genesishealth.apps.pharmacy.models import PharmacyPartner
from genesishealth.apps.products.models import ProductType
from genesishealth.apps.utils.class_views import GenesisFormView
from genesishealth.apps.utils.forms import GenesisForm
from genesishealth.apps.utils.func import read_csv_file
from genesishealth.apps.utils.request import require_admin_permission


test = require_admin_permission('pharmacy')


class ImportOrdersForm(GenesisForm):
    csv = forms.FileField(label="Order Import File")

    CSV_FIELD_NAMES = (
        'patient_id', 'product_id', 'quantity'
    )

    def clean_csv(self):
        data = read_csv_file(self.cleaned_data['csv'], self.CSV_FIELD_NAMES)
        self.order_data = {}
        products = {}
        errors = []
        for idx, row in enumerate(data):
            try:
                patient = User.objects.filter(
                    patient_profile__isnull=False).get(pk=row['patient_id'])
            except User.DoesNotExist:
                errors.append("Row {0}: Invalid patient id {1}".format(
                    idx, row['patient_id']))
            if row['product_id'] not in products:
                try:
                    product = ProductType.objects.get(
                        id=row['product_id'])
                except ProductType.DoesNotExist:
                    errors.append("Row {0}: Invalid product id {1}".format(
                        idx, row['product_id']))
                else:
                    products[row['product_id']] = product
            try:
                quantity = int(row['quantity'])
            except ValueError:
                errors.append("Row {0}: Invalid quantity {1}".format(
                    idx, row['quantity']))
            if errors:
                continue
            if patient.id not in self.order_data:
                self.order_data[patient.id] = {
                    'patient': patient,
                    'products': [],
                }
            self.order_data[patient.id]['products'].append((product, quantity))
        if errors:
            raise forms.ValidationError("\n".join(errors))
        return self.cleaned_data['csv']


class ImportOrdersView(GenesisFormView):
    form_class = ImportOrdersForm
    go_back_until = ['pharmacy:index']
    success_message = "The orders have been imported."

    def form_valid(self, form):
        for row in form.order_data.values():
            order = Order.objects.create(
                patient=row['patient'],
                added_by=self.request.user,
                order_status=Order.ORDER_STATUS_WAITING_FOR_RX,
                order_type=Order.ORDER_TYPE_PATIENT,
                order_origin=Order.ORDER_ORIGIN_BATCH_IMPORT,
                rx_partner=self.get_rx_partner()
            )
            for product, quantity in row['products']:
                OrderEntry.objects.create(
                    order=order,
                    quantity=quantity,
                    product=product)
        return super(ImportOrdersView, self).form_valid(form)

    def _get_page_title(self):
        return "Import Orders for Rx Partner {0}".format(
            self.get_rx_partner().name)

    def get_rx_partner(self):
        if not hasattr(self, '_rx_partner'):
            self._rx_partner = PharmacyPartner.objects.get(
                id=self.kwargs['rx_partner_id'])
        return self._rx_partner

main = test(ImportOrdersView.as_view())
