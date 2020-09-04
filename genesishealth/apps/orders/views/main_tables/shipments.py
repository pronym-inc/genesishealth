from genesishealth.apps.orders.models import OrderShipment
from genesishealth.apps.utils.class_views import (
    ActionItem, ActionTableColumn, AttributeTableColumn,
    GenesisTableLink, GenesisTableLinkAttrArg, GenesisTableView)
from genesishealth.apps.utils.request import require_admin_permission


test = require_admin_permission('orders')


class ShipmentView(GenesisTableView):
    page_title = "Manage Shipments"

    extra_search_fields = ['order__patient__patient_profile__insurance_identifier']

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
            AttributeTableColumn(
                "Employer / Group",
                "order.patient.patient_profile.company.name"),
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
        return OrderShipment.objects.all()


main = test(ShipmentView.as_view())
