from django.db.models import Q

from genesishealth.apps.orders.models import Order
from genesishealth.apps.utils.class_views import (
    ActionItem, ActionTableColumn, AttributeTableColumn,
    GenesisTableLink, GenesisTableLinkAttrArg, GenesisTableView)
from genesishealth.apps.utils.request import require_admin_permission


test = require_admin_permission('orders')


class OpenOrdersView(GenesisTableView):
    page_title = "Orders Waiting to be Shipped"

    def create_columns(self):
        return [
            AttributeTableColumn(
                "Order Created",
                'datetime_added',
                searchable=False,
                default_sort_direction='desc',
                default_sort=True
            ),
            AttributeTableColumn(
                "Patient",
                'patient.get_reversed_name',
                proxy_field='patient.last_name'),
            AttributeTableColumn('Rx Partner', 'rx_partner.name'),
            AttributeTableColumn("Order Type", 'get_order_type_display'),
            AttributeTableColumn(
                "Employer / Group", "patient.patient_profile.company.name"),
            ActionTableColumn(
                "Claim",
                actions=[
                    ActionItem(
                        'Claim Order',
                        GenesisTableLink(
                            'orders:claim',
                            url_args=[GenesisTableLinkAttrArg('id')]
                        ))
                ]
            )
        ]

    def get_queryset(self):
        return Order.objects.filter(
            order_status=Order.ORDER_STATUS_WAITING_TO_BE_SHIPPED).filter(
            Q(locked_by__isnull=True) | Q(locked_by=self.request.user))


main = test(OpenOrdersView.as_view())
