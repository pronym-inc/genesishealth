from django.urls import reverse

from genesishealth.apps.nursing.models import NursingGroup
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.class_views import (
    GenesisAboveTableButton, GenesisBaseDetailPane, GenesisDetailView)
from genesishealth.apps.utils.request import require_admin_permission


test = require_admin_permission('manage-business-partners')


class NursingGroupInformationPane(GenesisBaseDetailPane):
    template_name = "nursing/detail/panes/information.html"
    pane_title = "Information"


class NursingGroupDetailView(GenesisDetailView):
    pane_classes = (NursingGroupInformationPane,)

    def get_breadcrumbs(self):
        return [
            Breadcrumb('Nursing Groups',
                       reverse('nursing:index'))]

    def get_buttons(self):
        nursing_group = self.get_nursing_group()
        buttons = [
            GenesisAboveTableButton(
                'Edit Details',
                reverse('nursing:edit',
                        args=[nursing_group.id])),
        ]
        return buttons

    def get_nursing_group(self):
        if not hasattr(self, '_nursing_group'):
            self._nursing_group = NursingGroup.objects.get(
                pk=self.kwargs['nursing_group_id'])
        return self._nursing_group

    def get_page_title(self):
        return "Manage Nursing Group {0}".format(
            self.get_nursing_group())

    def get_pane_context(self):
        return {
            'nursing_group': self.get_nursing_group()
        }


main = test(NursingGroupDetailView.as_view())
