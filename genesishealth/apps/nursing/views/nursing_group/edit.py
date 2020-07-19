from genesishealth.apps.nursing.breadcrumbs import (
    get_nursing_group_breadcrumbs)
from genesishealth.apps.nursing.models import NursingGroup
from genesishealth.apps.utils.class_views import GenesisFormView
from genesishealth.apps.utils.forms import GenesisModelForm
from genesishealth.apps.utils.request import require_admin_permission


test = require_admin_permission('manage-business-partners')


class EditNursingGroupForm(GenesisModelForm):
    class Meta:
        model = NursingGroup
        fields = (
            'name', 'address', 'address2', 'city', 'zip', 'state',
            'contact_name', 'phone_number', 'epc_identifier')


class EditNursingGroupView(GenesisFormView):
    form_class = EditNursingGroupForm
    go_back_until = ['nursing:details']
    success_message = "The nursing group has been updated."

    def _get_breadcrumbs(self):
        return get_nursing_group_breadcrumbs(
            self.get_nursing_group(), self.request.user)

    def get_form_kwargs(self):
        kwargs = super(EditNursingGroupView, self).get_form_kwargs()
        kwargs['instance'] = self.get_nursing_group()
        return kwargs

    def get_nursing_group(self):
        if not hasattr(self, '_nursing_group'):
            self._nursing_group = NursingGroup.objects.get(
                pk=self.kwargs['nursing_group_id'])
        return self._nursing_group

    def _get_page_title(self):
        return "Edit Nursing Group {0}".format(
            self.get_nursing_group())


main = test(EditNursingGroupView.as_view())
