from datetime import timedelta

from django.utils.timezone import now

from genesishealth.apps.orders.models import OrderShipment
from genesishealth.apps.utils.class_views import (
    ActionItem, ActionTableColumn, AttributeTableColumn,
    GenesisTableLink, GenesisTableLinkAttrArg, GenesisTableView)
from genesishealth.apps.utils.request import require_admin_permission


test = require_admin_permission('orders')


class ShippingHistoryView(GenesisTableView):
    page_title = "Shipping History"

    extra_search_fields = [
        'tracking_number'
    ]

    def create_columns(self):
        return [
            AttributeTableColumn(
                "Shipment Created",
                'shipped_date',
                searchable=False,
                default_sort_direction='desc',
                default_sort=True
            ),
            AttributeTableColumn(
                "Patient",
                'order.patient.get_reversed_name',
                proxy_field='order.patient.last_name'),
            AttributeTableColumn('Rx Partner', 'order.rx_partner.name'),
            AttributeTableColumn("Order Type", 'order.get_order_type_display'),
            AttributeTableColumn("Category", 'order.category.name'),
            AttributeTableColumn(
                "Employer / Group",
                "order.patient.patient_profile.company.name"),
            AttributeTableColumn("Tracking Number", "tracking_number"),
            ActionTableColumn(
                "Details",
                actions=[
                    ActionItem(
                        'Details',
                        GenesisTableLink(
                            'orders:details',
                            url_args=[GenesisTableLinkAttrArg('order.id')]
                        ))
                ]
            ),
            ActionTableColumn(
                "Edit Shipment",
                actions=[
                    ActionItem(
                        'Edit Shipment',
                        GenesisTableLink(
                            'orders:edit-shipment',
                            url_args=[GenesisTableLinkAttrArg('id')]
                        ))
                ]
            ),
            ActionTableColumn(
                "Packing List",
                actions=[
                    ActionItem(
                        'Packing List',
                        GenesisTableLink(
                            'orders:shipment-packing-list',
                            url_args=[GenesisTableLinkAttrArg('order.id')],
                            prefix=''
                        ))
                ]
            )
        ]

    def get_queryset(self):
        return OrderShipment.objects.filter(
            tracking_number__isnull=False,
            shipped_date__gte=now() - timedelta(days=1))


main = test(ShippingHistoryView.as_view())
