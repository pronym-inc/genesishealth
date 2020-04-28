from django.urls import reverse
from django.http import HttpResponse
from django.views.generic import View

from genesishealth.apps.orders.models import Order
from genesishealth.apps.utils.request import (
    genesis_redirect, require_admin_permission)


test = require_admin_permission('orders')


class UnholdOrderView(View):
    def error(self, message):
        return HttpResponse(status=500)

    def get(self, request, *args, **kwargs):
        order = Order.objects.get(id=kwargs['order_id'])
        if not order.can_be_unheld():
            return self.error("Cannot unhold!")
        order.unhold()
        return genesis_redirect(
            self.request,
            reverse("orders:details", args=[order.id]))


main = test(UnholdOrderView.as_view())
