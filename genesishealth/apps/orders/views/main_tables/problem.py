from genesishealth.apps.orders.models import Order
from genesishealth.apps.utils.class_views import (
    ActionItem, ActionTableColumn, AttributeTableColumn,
    GenesisTableLink, GenesisTableLinkAttrArg, GenesisTableView)
from genesishealth.apps.utils.request import require_admin_permission


test = require_admin_permission('orders')


class ProblemOrderView(GenesisTableView):
    page_title = "Manage Problem Orders"

    extra_search_fields = ['patient__patient_profile__insurance_identifier']

    def create_columns(self):
        return [
            AttributeTableColumn(
                "Datetime Added",
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
                "Details",
                actions=[
                    ActionItem(
                        'Details',
                        GenesisTableLink(
                            'orders:details',
                            url_args=[GenesisTableLinkAttrArg('id')]
                        ))
                ]
            )
        ]

    def get_queryset(self):
        return Order.objects.filter(order_status=Order.ORDER_STATUS_PROBLEM)


main = test(ProblemOrderView.as_view())
