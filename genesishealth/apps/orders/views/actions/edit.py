from genesishealth.apps.orders.breadcrumbs import get_order_breadcrumbs
from genesishealth.apps.orders.models import Order
from genesishealth.apps.utils.class_views import GenesisFormView
from genesishealth.apps.utils.forms import GenesisModelForm
from genesishealth.apps.utils.request import require_admin_permission


test = require_admin_permission('orders')


class EditOrderForm(GenesisModelForm):
    class Meta:
        model = Order
        fields = ('order_notes',)


class EditOrderView(GenesisFormView):
    form_class = EditOrderForm
    go_back_until = ['orders:shipments']
    success_message = "The shipment has been updated."

    def get_breadcrumbs(self):
        return get_order_breadcrumbs(self.get_order(), self.request.user)

    def get_form_kwargs(self):
        kwargs = super(EditOrderView, self).get_form_kwargs()
        kwargs['instance'] = self.get_order()
        return kwargs

    def get_order(self):
        if not hasattr(self, '_order'):
            self._order = Order.objects.get(pk=self.kwargs['order_id'])
        return self._order

    def get_page_title(self):
        order = self.get_order()
        if order.is_patient_order():
            return "Edit Order #{0} for {1}".format(
                order.id, order.patient.get_reversed_name())
        return "Edit Order #{0} for {1}".format(
            order.id, order.rx_partner.name)


main = test(EditOrderView.as_view())
