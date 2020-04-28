from django.contrib.auth.decorators import login_required, user_passes_test

from genesishealth.apps.epc.models import EPCLogEntry
from genesishealth.apps.utils.class_views import (
    GenesisTableView, AttributeTableColumn)
from genesishealth.apps.utils.request import admin_user


admin_test = user_passes_test(admin_user)


class EPCLogEntryTableView(GenesisTableView):
    def create_columns(self):
        return [
            AttributeTableColumn(
                'Datetime',
                'datetime_added',
                default_sort=True,
                default_sort_direction='desc'),
            AttributeTableColumn(
                'Transaction Type',
                'transaction_type',
                searchable=False,
                sortable=False),
            AttributeTableColumn(
                'Source',
                'source',
                searchable=False,
                sortable=False),
            AttributeTableColumn(
                'Content',
                'content',
                searchable=False,
                sortable=False),
            AttributeTableColumn(
                'Response Sent',
                'response_sent',
                searchable=False,
                sortable=False),
            AttributeTableColumn(
                'EPC Member ID',
                'epc_member.epc_member_identifier',
                sortable=False),
            AttributeTableColumn(
                'GHT ID',
                'epc_member.user.id',
                sortable=False),
            AttributeTableColumn(
                'Success?',
                'is_successful',
                searchable=False,
                sortable=False)
        ]

    def get_page_title(self):
        return 'EPC Inbound API Log'

    def get_queryset(self):
        return EPCLogEntry.objects.all()


log_table = login_required(
    admin_test(EPCLogEntryTableView.as_view()))
