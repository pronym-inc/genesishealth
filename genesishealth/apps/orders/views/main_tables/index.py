from genesishealth.apps.orders.models import Order
from genesishealth.apps.utils.class_views import (
    ActionItem, ActionTableColumn,
    AttributeTableColumn, GenesisTableLink,
    GenesisTableLinkAttrArg, GenesisTableView)
from genesishealth.apps.utils.request import require_admin_permission


test = require_admin_permission('orders')


class OrderTableView(GenesisTableView):
    page_title = "Manage Orders"

    extra_search_fields = ['shipments__tracking_number']

    def create_columns(self):
        return [
            AttributeTableColumn('Datetime Added', 'datetime_added'),
            AttributeTableColumn(
                'Patient',
                'patient.get_reversed_name',
                proxy_field='patient.last_name'),
            AttributeTableColumn('Rx Partner', 'rx_partner.name'),
            AttributeTableColumn('Category', 'category.name'),
            AttributeTableColumn(
                'Order Status',
                'get_order_status_display',
                proxy_field='order_status'),
            AttributeTableColumn(
                'Order Type',
                'get_order_type_display',
                proxy_field='order_type'),
            ActionTableColumn(
                "Details",
                actions=[
                    ActionItem(
                        'Details',
                        GenesisTableLink(
                            'orders:details',
                            url_args=[GenesisTableLinkAttrArg('pk')]
                        ))
                ]
            )
        ]

    def get_queryset(self):
        return Order.objects.all()


main = test(OrderTableView.as_view())
