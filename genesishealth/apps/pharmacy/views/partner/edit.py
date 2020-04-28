from genesishealth.apps.pharmacy.breadcrumbs import get_rx_partner_breadcrumbs
from genesishealth.apps.pharmacy.models import PharmacyPartner
from genesishealth.apps.utils.class_views import GenesisFormView
from genesishealth.apps.utils.forms import GenesisModelForm
from genesishealth.apps.utils.request import require_admin_permission


test = require_admin_permission('manage-business-partners')


class EditRxPartnerForm(GenesisModelForm):
    class Meta:
        model = PharmacyPartner
        fields = (
            'name', 'address', 'address2', 'city', 'zip', 'state',
            'contact_name', 'phone_number', 'epc_identifier')


class EditRxPartnerView(GenesisFormView):
    form_class = EditRxPartnerForm
    go_back_until = ['pharmacy:details']
    success_message = "The pharmacy partner has been updated."

    def get_breadcrumbs(self):
        return get_rx_partner_breadcrumbs(
            self.get_rx_partner(), self.request.user)

    def get_form_kwargs(self):
        kwargs = super(EditRxPartnerView, self).get_form_kwargs()
        kwargs['instance'] = self.get_rx_partner()
        return kwargs

    def get_rx_partner(self):
        if not hasattr(self, '_rx_partner'):
            self._rx_partner = PharmacyPartner.objects.get(
                pk=self.kwargs['rx_partner_id'])
        return self._rx_partner

    def get_page_title(self):
        return "Edit Pharmacy Partner {0}".format(
            self.get_rx_partner())


main = test(EditRxPartnerView.as_view())
