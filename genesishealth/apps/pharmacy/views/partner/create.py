from django.urls import reverse

from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.pharmacy.models import PharmacyPartner
from genesishealth.apps.utils.class_views import GenesisFormView
from genesishealth.apps.utils.forms import GenesisModelForm
from genesishealth.apps.utils.request import require_admin_permission


test = require_admin_permission('manage-business-partners')


class PharmacyPartnerForm(GenesisModelForm):
    class Meta:
        model = PharmacyPartner
        fields = (
            'name', 'address', 'address2', 'city', 'zip', 'state',
            'contact_name', 'phone_number', 'epc_identifier')


class CreatePharmacyPartnerView(GenesisFormView):
    form_class = PharmacyPartnerForm
    go_back_until = ['pharmacy:index']
    success_message = "The pharmacy partner has been created."
    page_title = "Create Pharmacy Partner"

    def get_breadcrumbs(self):
        return [
            Breadcrumb('Pharmacy Partners',
                       reverse('pharmacy:index'))]


main = test(CreatePharmacyPartnerView.as_view())
