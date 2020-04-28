from django.urls import reverse
from django.http import HttpResponse
from django.views.generic import View

from genesishealth.apps.orders.models import Order
from genesishealth.apps.utils.request import (
    genesis_redirect, require_admin_permission)


test = require_admin_permission('orders')


class ClaimOrderView(View):
    def error(self, message):
        return HttpResponse(status=500)

    def get(self, request, *args, **kwargs):
        order = Order.objects.get(id=kwargs['order_id'])
        if order.order_status != Order.ORDER_STATUS_WAITING_TO_BE_SHIPPED:
            return self.error("Improper order state.")
        order.lock(self.request.user)
        return genesis_redirect(
            self.request,
            reverse("orders:create-shipment", args=[order.id]))


main = test(ClaimOrderView.as_view())
