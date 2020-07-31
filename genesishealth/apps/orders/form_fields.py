from json import loads

from django import forms
from django.forms.widgets import Input

from genesishealth.apps.orders.models import OrderEntry, OrderShipmentEntry
from genesishealth.apps.products.models import ProductType
from genesishealth.apps.utils.forms import GenesisModelForm


class OrderProductForm(GenesisModelForm):
    class Meta:
        model = OrderEntry
        fields = ('product', 'quantity')


class PackingProductForm(forms.ModelForm):
    class Meta:
        model = OrderShipmentEntry
        fields = (
            'product', 'quantity', 'expiration', 'inventory_identifier')


class SelectProductsWidget(Input):
    template_name = 'orders/widgets/select_products.html'
    input_type = 'text'
    order_product_form_class = OrderProductForm

    class Media:
        js = ('pages/orders/select_product.js',)

    def __init__(self, *args, **kwargs):
        self.is_bulk = kwargs.pop('is_bulk', False)
        super(SelectProductsWidget, self).__init__(*args, **kwargs)

    def get_context(self, *args, **kwargs):
        ctx = super(SelectProductsWidget, self).get_context(*args, **kwargs)
        ctx['products'] = self.get_products()
        return ctx

    def get_products(self):
        return ProductType.objects.filter(is_bulk=False)


class SelectProductsBulkWidget(SelectProductsWidget):
    def get_products(self):
        return ProductType.objects.filter(is_bulk=True)


class SelectProductsPackingWidget(SelectProductsWidget):
    order_product_form_class = PackingProductForm


class SelectProductsField(forms.Field):
    widget = SelectProductsWidget()

    def prepare_value(self, value):
        return value

    def to_python(self, value):
        if not value:
            return []
        parsed = loads(value)
        form_fields = OrderProductForm.Meta.fields
        output = []
        for row in parsed:
            # Make sure only appropriate fields find their way in.
            data = {k: v for k, v in row.items() if k in form_fields}
            f = OrderProductForm(data)
            if f.is_valid():
                output.append(f.save(commit=False))
        return output


class SelectPackingProductsField(SelectProductsField):
    widget = SelectProductsPackingWidget
