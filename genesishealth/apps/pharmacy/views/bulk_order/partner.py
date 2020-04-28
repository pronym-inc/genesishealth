from django.urls import reverse

from genesishealth.apps.pharmacy.models import PharmacyPartner
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.class_views import (
    ActionItem, ActionTableColumn,
    AttributeTableColumn, GenesisAboveTableButton, GenesisTableLink,
    GenesisTableLinkAttrArg, GenesisTableView)
from genesishealth.apps.utils.request import require_admin_permission


test = require_admin_permission('pharmacy')


class PharmacyPartnerTableView(GenesisTableView):
    page_title = "Manage Pharmacy Partners"

    def create_columns(self):
        return [
            AttributeTableColumn(
                'Datetime Added',
                'datetime_added',
                default_sort=True,
                default_sort_direction='desc'),
            AttributeTableColumn(
                'Status',
                'get_order_status_display',
                proxy_field='order_status'),
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

    def get_above_table_items(self):
        rx_partner = self.get_rx_partner()
        return [
            GenesisAboveTableButton(
                'Create New',
                reverse('pharmacy:create-bulk-order',
                        args=[rx_partner.id]))
        ]

    def get_breadcrumbs(self):
        rx_partner = self.get_rx_partner()
        return [
            Breadcrumb('Pharmacy Partners',
                       reverse('pharmacy:index')),
            Breadcrumb('Pharmacy Partner: {0}'.format(rx_partner),
                       reverse('pharmacy:details', args=[rx_partner.id]))]

    def get_rx_partner(self):
        if not hasattr(self, '_rx_partner'):
            self._rx_partner = PharmacyPartner.objects.get(
                pk=self.kwargs['rx_partner_id'])
        return self._rx_partner

    def get_queryset(self):
        return self.get_rx_partner().orders.all()
main = test(PharmacyPartnerTableView.as_view())
