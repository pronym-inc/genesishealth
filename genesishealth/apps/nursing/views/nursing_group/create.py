from django.urls import reverse

from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.nursing.models import NursingGroup
from genesishealth.apps.utils.class_views import GenesisFormView
from genesishealth.apps.utils.forms import GenesisModelForm
from genesishealth.apps.utils.request import require_admin_permission


test = require_admin_permission('manage-business-partners')


class NursingGroupForm(GenesisModelForm):
    class Meta:
        model = NursingGroup
        fields = (
            'name', 'address', 'address2', 'city', 'zip', 'state',
            'contact_name', 'phone_number', 'epc_identifier')


class CreateNursingGroupView(GenesisFormView):
    form_class = NursingGroupForm
    go_back_until = ['nursing:index']
    success_message = "The nursing group has been created."
    page_title = "Create Nursing Group"

    def _get_breadcrumbs(self):
        return [
            Breadcrumb('Nursing Groups',
                       reverse('nursing:index'))]


main = test(CreateNursingGroupView.as_view())
