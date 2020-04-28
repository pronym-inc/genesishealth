from django.views.generic import TemplateView

from genesishealth.apps.orders.models import OrderShipment
from genesishealth.apps.utils.request import require_admin_permission


test = require_admin_permission('orders')


class ShipmentLabelView(TemplateView):
    template_name = "orders/shipment_label.html"

    def get_context_data(self, **kwargs):
        kwargs['shipment'] = self.get_shipment()
        kwargs['title'] = self.get_page_title()
        return super(ShipmentLabelView, self).get_context_data(**kwargs)

    def get_shipment(self):
        if not hasattr(self, '_shipment'):
            self._shipment = OrderShipment.objects.get(
                pk=self.kwargs['shipment_id'])
        return self._shipment

    def get_page_title(self):
        order = self.get_shipment().order
        return "Shipment Label for Order #{0}".format(order.id)


main = test(ShipmentLabelView.as_view())
