from genesishealth.apps.orders.models import Order
from genesishealth.apps.utils.class_views import (
    ActionItem, ActionTableColumn, AttributeTableColumn,
    GenesisTableLink, GenesisTableLinkAttrArg, GenesisTableView)
from genesishealth.apps.utils.request import require_admin_permission


test = require_admin_permission('orders')


class WorklistView(GenesisTableView):
    page_title = "Order Worklist"

    extra_search_fields = ['patient__patient_profile__insurance_identifier']

    def create_columns(self):
        return [
            AttributeTableColumn(
                "Patient",
                'patient.get_reversed_name',
                proxy_field='patient.last_name'),
            AttributeTableColumn(
                "Order Created",
                'datetime_added',
                searchable=False
            ),
            AttributeTableColumn("Order Type", 'get_order_type_display'),
            AttributeTableColumn('Rx Partner', 'rx_partner.name'),
            AttributeTableColumn(
                "Employer / Group", "patient.patient_profile.company.name"),
            ActionTableColumn(
                "Details",
                actions=[
                    ActionItem(
                        'Details',
                        GenesisTableLink(
                            'orders:details',
                            url_args=[GenesisTableLinkAttrArg('id')]
                        )),
                    ActionItem(
                        'Create Shipment',
                        GenesisTableLink(
                            'orders:create-shipment',
                            url_args=[GenesisTableLinkAttrArg('id')]
                        ))
                ]
            )
        ]

    def get_queryset(self):
        return Order.objects.filter(
            order_status=Order.ORDER_STATUS_IN_PROGRESS,
            locked_by=self.request.user)


main = test(WorklistView.as_view())
