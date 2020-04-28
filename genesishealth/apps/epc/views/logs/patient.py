# pragma: no cover
from django.contrib.auth.decorators import login_required, user_passes_test

from genesishealth.apps.epc.models import PatientRequestTransaction
from genesishealth.apps.utils.class_views import (
    GenesisTableView, AttributeTableColumn)
from genesishealth.apps.utils.request import admin_user


admin_test = user_passes_test(admin_user)


class EPCPatientLogTableView(GenesisTableView):
    fake_count = True

    def create_columns(self):
        return [
            AttributeTableColumn(
                'Datetime', 'datetime_added',
                default_sort=True,
                default_sort_direction='desc'),
            AttributeTableColumn(
                'Raw Request',
                'raw_request',
                sortable=False),
            AttributeTableColumn(
                'Success?',
                'is_successful',
                sortable=False)
        ]

    def get_page_title(self):
        return 'EPC Patient Log'

    def get_queryset(self):
        return PatientRequestTransaction.objects.all()
patient_log = login_required(
    admin_test(EPCPatientLogTableView.as_view()))
