from django.urls import reverse

from genesishealth.apps.nursing.models import NursingGroup
from genesishealth.apps.utils.class_views import (
    ActionItem, ActionTableColumn,
    AttributeTableColumn, GenesisAboveTableButton, GenesisTableLink,
    GenesisTableLinkAttrArg, GenesisTableView)
from genesishealth.apps.utils.request import require_admin_permission


test = require_admin_permission('manage-business-partners')


class NursingGroupTableView(GenesisTableView):
    page_title = "Manage Nursing Group"

    def create_columns(self):
        return [
            AttributeTableColumn('EPC Identifier', 'epc_identifier'),
            AttributeTableColumn('Name', 'name'),
            AttributeTableColumn(
                'Address', 'get_full_address', searchable=False),
            AttributeTableColumn('City', 'city', searchable=False),
            AttributeTableColumn('State', 'state', searchable=False),
            AttributeTableColumn('ZIP', 'zip', searchable=False),
            AttributeTableColumn('Contact', 'contact_name', searchable=False),
            AttributeTableColumn(
                'Phone Number', 'phone_number', searchable=False),
            ActionTableColumn(
                "Details",
                actions=[
                    ActionItem(
                        'Details',
                        GenesisTableLink(
                            'nursing:details',
                            url_args=[GenesisTableLinkAttrArg('pk')]
                        ))
                ]
            ),
        ]

    def get_above_table_items(self):
        return [
            GenesisAboveTableButton(
                'Create New',
                reverse('nursing:create'))
        ]

    def get_queryset(self):
        return NursingGroup.objects.all()


main = test(NursingGroupTableView.as_view())
