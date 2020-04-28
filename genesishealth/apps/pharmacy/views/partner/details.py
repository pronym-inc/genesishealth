from django.urls import reverse

from genesishealth.apps.pharmacy.models import PharmacyPartner
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.class_views import (
    GenesisAboveTableButton, GenesisBaseDetailPane, GenesisDetailView)
from genesishealth.apps.utils.request import require_admin_permission


test = require_admin_permission('manage-business-partners')


class RxPartnerInformationPane(GenesisBaseDetailPane):
    template_name = "pharmacy/detail/panes/information.html"
    pane_title = "Information"


class RxPartnerDetailView(GenesisDetailView):
    pane_classes = (RxPartnerInformationPane,)

    def get_breadcrumbs(self):
        return [
            Breadcrumb('Pharmacy Partners',
                       reverse('pharmacy:index'))]

    def get_buttons(self):
        rx_partner = self.get_rx_partner()
        buttons = [
            GenesisAboveTableButton(
                'Edit Details',
                reverse('pharmacy:edit',
                        args=[rx_partner.id])),
            GenesisAboveTableButton(
                'Bulk Orders',
                reverse('pharmacy:partner-bulk-orders',
                        args=[rx_partner.id])),
            GenesisAboveTableButton(
                'Bulk Order History',
                reverse('orders:rx-partner-order-report',
                        args=[rx_partner.id])),
            GenesisAboveTableButton(
                'Import Orders',
                reverse('pharmacy:import-orders',
                        args=[rx_partner.id])),
            GenesisAboveTableButton(
                'Fulfill Orders',
                reverse('pharmacy:fulfill-orders',
                        args=[rx_partner.id]))
        ]
        return buttons

    def get_rx_partner(self):
        if not hasattr(self, '_rx_partner'):
            self._rx_partner = PharmacyPartner.objects.get(
                pk=self.kwargs['rx_partner_id'])
        return self._rx_partner

    def get_page_title(self):
        return "Manage Pharmacy Partner {0}".format(
            self.get_rx_partner())

    def get_pane_context(self):
        return {
            'rx_partner': self.get_rx_partner()
        }
main = test(RxPartnerDetailView.as_view())
