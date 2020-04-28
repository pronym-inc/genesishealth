from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User

from genesishealth.apps.accounts.breadcrumbs.patients import (
    get_patient_breadcrumbs)
from genesishealth.apps.epc.models import EPCOrder
from genesishealth.apps.utils.class_views import (
    ActionItem, ActionTableColumn, GenesisTableView, AttributeTableColumn,
    GenesisTableLink, GenesisTableLinkAttrArg)
from genesishealth.apps.utils.request import admin_user


admin_test = user_passes_test(admin_user)


class EPCOrderTableView(GenesisTableView):
    fake_count = True

    def create_columns(self):
        return [
            AttributeTableColumn(
                'Order No', 'order_number',
                default_sort=True,
                default_sort_direction='desc'),
            AttributeTableColumn(
                'Order Date',
                'order_date',
                searchable=False),
            AttributeTableColumn(
                'Meter',
                'meter_request',
                sortable=False,
                searchable=False),
            AttributeTableColumn(
                'Strips',
                'strips_request',
                sortable=False,
                searchable=False),
            AttributeTableColumn(
                'Lancets',
                'lancet_request',
                sortable=False,
                searchable=False),
            AttributeTableColumn(
                'Control Solution',
                'control_solution_request',
                sortable=False,
                searchable=False),
            AttributeTableColumn(
                'Lancing Device',
                'lancing_device_request',
                sortable=False,
                searchable=False),
            AttributeTableColumn(
                'Order Type',
                'order_type',
                sortable=False),
            AttributeTableColumn(
                'Status',
                'order_status',
                sortable=False),
            AttributeTableColumn(
                'Ship Date',
                'ship_date',
                searchable=False),
            ActionTableColumn(
                "Actions",
                actions=[
                    ActionItem(
                        'Details',
                        GenesisTableLink(
                            'epc:patient-orders-details',
                            url_args=[GenesisTableLinkAttrArg('pk')]
                        ))
                ]
            ),

        ]

    def get_breadcrumbs(self):
        patient = self.get_patient()
        return get_patient_breadcrumbs(
            patient, self.request.user, include_detail=True)

    def get_page_title(self):
        patient = self.get_patient()
        return 'EPC Order Log for {0}'.format(patient.get_reversed_name())

    def get_patient(self):
        if not hasattr(self, '_patient'):
            print(self.kwargs)
            self._patient = User.objects.filter(
                patient_profile__isnull=False).get(
                pk=self.kwargs['patient_id'])
        return self._patient

    def get_queryset(self):
        patient = self.get_patient()
        return EPCOrder.objects.filter(epc_member=patient.patient_profile)


patient_orders = login_required(
    admin_test(EPCOrderTableView.as_view()))
