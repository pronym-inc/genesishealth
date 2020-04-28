from django.urls import reverse

from genesishealth.apps.accounts.breadcrumbs.patients import (
    get_patient_breadcrumbs)
from genesishealth.apps.orders.models import Order
from genesishealth.apps.pharmacy.breadcrumbs import get_rx_partner_breadcrumbs
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.class_views import (
    GenesisAboveTableButton, GenesisBaseDetailPane, GenesisDetailView)
from genesishealth.apps.utils.request import require_admin_permission


test = require_admin_permission('orders')


class OrderInformationPane(GenesisBaseDetailPane):
    template_name = "orders/details/panes/information.html"
    pane_title = "Information"


class OrderContentsPane(GenesisBaseDetailPane):
    template_name = "orders/details/panes/contents.html"
    pane_title = "Contents"


class OrderShipmentPane(GenesisBaseDetailPane):
    template_name = "orders/details/panes/shipment.html"
    pane_title = "Shipment"


class OrderDetailView(GenesisDetailView):
    pane_classes = (OrderInformationPane, OrderContentsPane, OrderShipmentPane)

    def get_breadcrumbs(self):
        order = self.get_order()
        if order.is_patient_order():
            patient = self.get_patient()
            breadcrumbs = get_patient_breadcrumbs(patient, self.request.user)
            breadcrumbs.append(
                Breadcrumb(
                    'Orders',
                    reverse('accounts:patient-orders', args=[patient.pk]))
            )
        else:
            rx_partner = self.get_rx_partner()
            breadcrumbs = get_rx_partner_breadcrumbs(
                rx_partner, self.request.user)
        return breadcrumbs

    def get_buttons(self):
        order = self.get_order()
        buttons = [
            GenesisAboveTableButton(
                'Edit',
                reverse('orders:edit', args=[order.pk])
            )
        ]
        if order.can_add_problem():
            buttons.append(GenesisAboveTableButton(
                'Add Problem',
                reverse('orders:create-problem', args=[order.pk])
            ))
        if order.can_be_held():
            buttons.append(GenesisAboveTableButton(
                'Place Hold',
                reverse('orders:hold', args=[order.pk])
            ))
        if order.can_be_canceled():
            buttons.append(GenesisAboveTableButton(
                'Cancel',
                reverse('orders:cancel', args=[order.pk])
            ))
        if order.can_be_unlocked():
            buttons.append(GenesisAboveTableButton(
                'Unlock',
                reverse('orders:unlock', args=[order.pk])
            ))
        if order.can_be_unheld():
            buttons.append(GenesisAboveTableButton(
                'Unhold',
                reverse('orders:unhold', args=[order.pk])
            ))
        if not order.is_locked:
            buttons.append(GenesisAboveTableButton(
                'Claim',
                reverse('orders:claim', args=[order.pk])
            ))
        if order.can_resolve_problem():
            buttons.append(GenesisAboveTableButton(
                'Resolve Problem',
                reverse('orders:resolve-problem', args=[order.pk])
            ))
        if order.has_shipping_label():
            buttons.append(GenesisAboveTableButton(
                'Show Shipping Label',
                order.get_shipping_label(),
                prefix=""))
        return buttons

    def get_order(self):
        if not hasattr(self, '_order'):
            self._order = Order.objects.get(pk=self.kwargs['order_id'])
        return self._order

    def get_patient(self):
        if not hasattr(self, '_patient'):
            self._patient = self.get_order().patient
        return self._patient

    def get_page_title(self):
        return "Order Details"

    def get_pane_context(self):
        return {'order': self.get_order()}

    def get_rx_partner(self):
        if not hasattr(self, '_rx_partner'):
            self._rx_partner = self.get_order().rx_partner
        return self._rx_partner


main = test(OrderDetailView.as_view())
