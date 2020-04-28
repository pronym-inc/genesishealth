from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse
from django.db.models import Q

from genesishealth.apps.accounts.views.base import GetGroupMixin
from genesishealth.apps.accounts.models import PatientProfile
from genesishealth.apps.gdrives.models import GDrive
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.class_views import (
    AttributeTableColumn,
    ActionTableColumn, ActionItem, GenesisTableLink, GenesisTableLinkAttrArg,
    GenesisAboveTableDropdown, GenesisAboveTableButton,
    GenesisDropdownOption, GenesisTableView, GenesisSingleTableBase,
    GenesisMultipleTableView, GenesisAboveTableRadio)
from genesishealth.apps.utils.request import check_user_type


class GetPatientMixin(object):
    def get_group(self):
        self.get_parent().get_group()

    def get_patient(self):
        self.get_parent().get_patient()


class CurrentDeviceTable(GenesisSingleTableBase, GetPatientMixin):
    header = "Current and Previous Devices"
    name_postfix = "patient-devices"

    def create_columns(self):
        parent = self.get_parent()
        patient = parent.get_patient()
        request = self.get_request()
        actions = []
        if request and request.user.is_superuser:
            actions.extend([
                ActionItem(
                    'Assign Device',
                    GenesisTableLink(
                        'gdrives:assign-to-patient',
                        url_args=[
                            GenesisTableLinkAttrArg('pk'), patient.pk]
                    ),
                    condition=['!patient']
                ),
                ActionItem(
                    'Unassign Device',
                    GenesisTableLink(
                        'gdrives:unassign',
                        url_args=[
                            GenesisTableLinkAttrArg('pk')]
                    ),
                    condition=['patient']
                )
            ])
        actions.append(
            ActionItem(
                'Details',
                GenesisTableLink(
                    'gdrives:detail',
                    url_args=[GenesisTableLinkAttrArg('pk')]))
        )
        return [
            AttributeTableColumn(
                'Device No',
                'ordinal',
                cell_class='main'),
            AttributeTableColumn('MEID', 'meid'),
            AttributeTableColumn('Serial #', 'device_id'),
            AttributeTableColumn(
                'Status',
                'get_status_display',
                proxy_field='status'),
            AttributeTableColumn(
                'Network Status',
                'get_network_status_display',
                proxy_field='network_status'),
            AttributeTableColumn('Assigned', 'datetime_assigned'),
            AttributeTableColumn('Replaced', 'datetime_replaced'),
            ActionTableColumn(
                'Actions',
                actions=actions
            )
        ]

    def get_queryset(self):
        patient = self.get_parent().get_patient()
        devices = patient.previous_devices.all()
        device = patient.patient_profile.get_device()
        if device:
            devices |= GDrive.objects.filter(pk=device.pk)
        return devices


class AvailableDeviceTable(GenesisSingleTableBase, GetPatientMixin):
    header = "Available Devices"
    name_postfix = "available-devices"

    def create_columns(self):
        parent = self.get_parent()
        patient = parent.get_patient()
        request = self.get_request()
        actions = []
        if request.user.is_superuser:
            actions.append(
                ActionItem(
                    'Assign Device',
                    GenesisTableLink(
                        'gdrives:assign-to-patient',
                        url_args=[
                            GenesisTableLinkAttrArg('pk'), patient.pk]
                    ),
                    condition=['!patient']
                )
            )
        return [
            AttributeTableColumn('MEID', 'meid'),
            AttributeTableColumn('Serial #', 'device_id'),
            AttributeTableColumn(
                'Warehouse Carton #', 'warehouse_carton.number'),
            AttributeTableColumn(
                'Lot #', 'manufacturer_carton.lot_number'),
            AttributeTableColumn('Last Reading',
                                 'last_reading.reading_datetime_utc'),
            ActionTableColumn(
                'Actions',
                actions=actions
            )
        ]

    def get_queryset(self):
        return GDrive.objects.filter(status=GDrive.DEVICE_STATUS_AVAILABLE)


class GDriveMultipleTableView(GenesisMultipleTableView, GetGroupMixin):
    table_classes = [CurrentDeviceTable, AvailableDeviceTable]

    def __init__(self, *args, **kwargs):
        self._patient = None
        self._group = None
        super(GDriveMultipleTableView, self).__init__(*args, **kwargs)

    def get_breadcrumbs(self):
        patient = self.get_patient()
        group = self.get_group()
        if self.request.user.is_admin():
            if group is None:
                return [
                    Breadcrumb('Users', reverse('accounts:manage-users')),
                    Breadcrumb(
                        'Patient: {0}'.format(patient.get_reversed_name()),
                        reverse('accounts:manage-patients-detail',
                                args=[patient.pk]))
                ]
            breadcrumbs = [
                Breadcrumb('Business Partners',
                           reverse('accounts:manage-groups')),
                Breadcrumb(
                    'Business Partner: {0}'.format(group.name),
                    reverse('accounts:manage-groups-detail',
                            args=[group.pk]))
            ]
            if patient is not None:
                breadcrumbs.extend([
                    Breadcrumb(
                        'Patients',
                        reverse('accounts:manage-groups-patients',
                                   args=[group.pk])),
                    Breadcrumb(
                        'Patient: {0}'.format(patient.get_reversed_name()),
                        reverse('accounts:manage-patients-detail',
                                args=[patient.pk]))
                ])
        else:
            breadcrumbs = [
                Breadcrumb('Patients', reverse('accounts:manage-patients'))
            ]
        return breadcrumbs

    def get_group(self, force=False):
        if force or self._group is None:
            self._group = super(GDriveMultipleTableView, self).get_group(force)
            if self._group is None:
                user = self.get_user()
                if user.is_professional():
                    self._group = user.professional_profile.parent_group
                else:
                    patient = self.get_patient()
                    self._group = patient.patient_profile.get_group()
        return self._group

    def get_page_title(self):
        patient = self.get_patient()
        if patient:
            return 'Manage Devices for {}'.format(patient.get_reversed_name())
        group = self.get_group()
        return 'Manage Devices for {}'.format(group)

    def get_patient(self):
        if self._patient is None:
            user = self.get_user()
            if user.is_admin():
                self._patient = PatientProfile.myghr_patients.get_users().get(
                    pk=self.kwargs['patient_id'])
            else:
                group = self.get_group()
                self._patient = group.get_patients().get(
                    pk=self.kwargs['patient_id'])
        return self._patient


test = user_passes_test(
    lambda u: check_user_type(u, ['Admin', 'Professional']))
patient_detail = test(GDriveMultipleTableView.as_view())


class BaseIndexDeviceTable(GenesisSingleTableBase):
    def create_columns(self):
        return [
            AttributeTableColumn('MEID', 'meid', cell_class='main'),
            AttributeTableColumn('Serial #', 'device_id'),
            AttributeTableColumn(
                'Group', 'group', hide_for_user_types=['professional']),
            # TODO: this column still being used?
            AttributeTableColumn('Status', 'network_status'),
            AttributeTableColumn(
                'Patient', 'patient.get_reversed_name', failsafe=''),
            AttributeTableColumn('Last Reading', 'get_last_reading_date'),
            ActionTableColumn(
                'Actions',
                actions=[
                    ActionItem(
                        'Edit Device',
                        GenesisTableLink(
                            'gdrives:edit',
                            url_args=[GenesisTableLinkAttrArg('pk')]
                        )
                    ),
                    ActionItem(
                        'Delete Device',
                        GenesisTableLink(
                            'gdrives:delete',
                            url_args=[GenesisTableLinkAttrArg('pk')]
                        )
                    ),
                    ActionItem(
                        'Assign Device',
                        GenesisTableLink(
                            'gdrives:assign',
                            url_args=[GenesisTableLinkAttrArg('pk')]
                        ),
                        condition=['!patient']
                    ),
                    ActionItem(
                        'Unassign Device',
                        GenesisTableLink(
                            'gdrives:unassign',
                            url_args=[GenesisTableLinkAttrArg('pk')]
                        ),
                        condition=['patient']
                    ),
                ]
            )
        ]

    def get_queryset(self):
        group = self._parent.get_group()
        if group:
            qs = group.gdrives.all()
        else:
            user = self.get_user()
            assert user.is_admin()
            qs = GDrive.objects.all()
        return qs.exclude(
            Q(is_verizon_testing_device=True) |
            Q(is_verizon_monitoring_device=True) |
            Q(is_scalability_device=True)
        )


class IndexAssignedTable(BaseIndexDeviceTable):
    header = 'Assigned Devices'
    name_postfix = 'assigned'
    force_batch = True

    def get_queryset(self):
        qs = super(IndexAssignedTable, self).get_queryset()
        return qs.filter(
            patient__isnull=False, assigned_at__isnull=False, demo=False)


class IndexUnassignedTable(BaseIndexDeviceTable):
    header = 'Unassigned Devices'
    name_postfix = 'unassigned'

    def get_queryset(self):
        qs = super(IndexUnassignedTable, self).get_queryset()
        return qs.filter(
            patient__isnull=True, assigned_at__isnull=True, demo=False)


class IndexDemoTable(BaseIndexDeviceTable):
    header = 'Demo Devices'
    name_postfix = 'demo'

    def get_queryset(self):
        qs = super(IndexDemoTable, self).get_queryset()
        return qs.filter(partner__isnull=True, demo=True)


class IndexPartnerTable(BaseIndexDeviceTable):
    header = 'Partner Devices'
    name_postfix = 'partner'

    def create_columns(self):
        columns = super(IndexPartnerTable, self).create_columns()
        new_columns = (
            columns[:3] +
            [AttributeTableColumn('Partner', 'partner')] +
            columns[3:]
        )
        return new_columns

    def get_queryset(self):
        qs = super(IndexPartnerTable, self).get_queryset()
        return qs.filter(partner__isnull=False)


class IndexMultipleTableView(GenesisMultipleTableView, GetGroupMixin):
    additional_css_templates = [('gdrives/filter_states_css.html',)],
    additional_js_templates = [('gdrives/filter_states_js.html',)]
    force_batch = True

    def get_above_table_items(self):
        items = []
        group = self.get_group()
        user = self.get_user()
        filter_options = [
            GenesisDropdownOption('Assigned', 'assigned'),
            GenesisDropdownOption('Unassigned', 'unassigned')
        ]
        dropdown_options = []
        if user.is_admin():
            filter_options.extend([
                GenesisDropdownOption('Demo', 'demo'),
                GenesisDropdownOption('Partner', 'partner')
            ])
            dropdown_options.extend([
                GenesisDropdownOption(
                    'Assign to Group', reverse('gdrives:batch-assign')),
                GenesisDropdownOption(
                    'Unassign From Group', reverse('gdrives:batch-unassign')),
                GenesisDropdownOption(
                    'Assign to API Partner',
                    reverse('gdrives:batch-assign-apipartner')),
                GenesisDropdownOption(
                    'Recover Readings',
                    reverse('gdrives:batch-recover-readings'))
            ])
            if group:
                add_link_name = 'accounts:manage-groups-devices-create'
                add_link_args = [group.id]
                import_link_name = 'accounts:manage-groups-devices-import-csv'
                import_link_args = [group.id]
            else:
                add_link_name = 'gdrives:new'
                add_link_args = []
                import_link_name = 'gdrives:import'
                import_link_args = []
            add_link = reverse(add_link_name, args=add_link_args)
            import_link = reverse(import_link_name, args=import_link_args)
            items.extend([
                GenesisAboveTableButton('Add Device', add_link),
                GenesisAboveTableButton('Import Devices CSV', import_link)
            ])
        dropdown_options.append(
            GenesisDropdownOption('Delete', reverse('gdrives:batch-delete')))
        items.append(GenesisAboveTableDropdown(dropdown_options))
        items.append(GenesisAboveTableRadio(filter_options))
        return items

    def get_breadcrumbs(self):
        group = self.get_group()
        if group is not None:
            return [
                Breadcrumb('Business Partners',
                           reverse('accounts:manage-groups')),
                Breadcrumb(
                    'Business Partner: {0}'.format(group.name),
                    reverse('accounts:manage-groups-detail',
                            args=[group.pk]))
            ]
        return []

    def get_page_title(self):
        group = self.get_group()
        if group:
            return 'Manage Devices for {}'.format(group)
        return 'Manage Devices'

    def get_table_classes(self):
        user = self.get_user()
        table_classes = [IndexAssignedTable, IndexUnassignedTable]
        if user.is_admin():
            table_classes.extend([IndexDemoTable, IndexPartnerTable])
        return table_classes


index = test(IndexMultipleTableView.as_view())


class AssignedDeviceTableView(GenesisTableView):
    def create_columns(self):
        return [
            AttributeTableColumn('MEID', 'meid'),
            AttributeTableColumn('Serial #', 'device_id'),
            AttributeTableColumn(
                'Patient',
                'patient.get_reversed_name',
                searchable=False,
                proxy_field='patient.last_name'),
            AttributeTableColumn(
                'Patient Status',
                'patient.patient_profile.get_account_status_display',
                searchable=False,
                proxy_field='patient.patient_profile.account_status'),
            AttributeTableColumn(
                'Last Reading',
                'get_last_reading_date',
                searchable=False,
                sortable=False
            ),
            AttributeTableColumn(
                'Device Status',
                'get_network_status_display',
                searchable=True,
                proxy_field='network_status'
            ),
            ActionTableColumn(
                'View',
                actions=[
                    ActionItem(
                        'View',
                        GenesisTableLink(
                            'gdrives:detail',
                            url_args=[GenesisTableLinkAttrArg('pk')]
                        )
                    )
                ]
            )
        ]

    def get_above_table_items(self):
        return [
            GenesisAboveTableDropdown(
                [
                    GenesisDropdownOption(
                        'Recover Readings',
                        reverse('gdrives:batch-recover-readings')),
                    GenesisDropdownOption(
                        'Mark Failed Delivery',
                        reverse('gdrives:batch-mark-failed-delivery')),
                    GenesisDropdownOption(
                        'Assign to Rx Partner',
                        reverse('gdrives:batch-assign-rx-partner'))
                ]
            )
        ]

    def get_page_title(self):
        return 'Manage Assigned Devices'

    def get_queryset(self):
        return GDrive.objects.filter(status=GDrive.DEVICE_STATUS_ASSIGNED)
assigned_devices = test(AssignedDeviceTableView.as_view())


class UnassignedDeviceTableView(GenesisTableView):
    def create_columns(self):
        return [
            AttributeTableColumn('MEID', 'meid'),
            AttributeTableColumn('Serial #', 'device_id'),
            AttributeTableColumn(
                'Patient',
                'last_assigned_patient.get_reversed_name',
                searchable=False,
                sortable=False,
                proxy_field='patient.last_name'),
            AttributeTableColumn(
                'Patient Status',
                'last_assigned_patient.patient_profile'
                '.get_account_status_display',
                searchable=False,
                proxy_field='last_assigned_patient.patient_profile.'
                            'account_status'),
            AttributeTableColumn(
                'Replaced Date',
                'datetime_replaced',
                searchable=False,
                sortable=False
            ),
            AttributeTableColumn(
                'Device Status',
                'get_status_display',
                searchable=False,
                proxy_field='status'
            ),
            AttributeTableColumn(
                'Network Status',
                'get_network_status_display',
                searchable=False,
                proxy_field='network_status'
            ),
            ActionTableColumn(
                'View',
                actions=[
                    ActionItem(
                        'View',
                        GenesisTableLink(
                            'gdrives:detail',
                            url_args=[GenesisTableLinkAttrArg('pk')]
                        )
                    )
                ]
            )
        ]

    def get_above_table_items(self):
        return [
            GenesisAboveTableDropdown(
                [
                    GenesisDropdownOption(
                        'Recover Readings',
                        reverse('gdrives:batch-recover-readings'))
                ]
            ),
            GenesisAboveTableButton(
                'RMA Determination Report',
                reverse('gdrives:configure-rma-summary-report')
            )
        ]

    def get_page_title(self):
        return 'Manage Unassigned Devices'

    def get_queryset(self):
        return GDrive.objects.filter(
            status__in=(GDrive.DEVICE_STATUS_UNASSIGNED,
                        GDrive.DEVICE_STATUS_FAILED_DELIVERY))
unassigned_devices = test(UnassignedDeviceTableView.as_view())


class AvailableDeviceTableView(GenesisTableView):
    def create_columns(self):
        return [
            AttributeTableColumn('MEID', 'meid'),
            AttributeTableColumn('Serial #', 'device_id'),
            AttributeTableColumn(
                'Warehouse Carton #', 'warehouse_carton.number'),
            AttributeTableColumn('Lot #', 'manufacturer_carton.lot_number'),
            AttributeTableColumn(
                'Last Reading',
                'last_reading.reading_datetime_utc',
                searchable=False,
                sortable=False),
            AttributeTableColumn(
                'Device Status',
                'get_network_status_display',
                searchable=False,
                proxy_field='network_status'
            ),
            ActionTableColumn(
                'View',
                actions=[
                    ActionItem(
                        'View',
                        GenesisTableLink(
                            'gdrives:detail',
                            url_args=[GenesisTableLinkAttrArg('pk')]
                        )
                    )
                ]
            )
        ]

    def get_above_table_items(self):
        return [
            GenesisAboveTableDropdown(
                [
                    GenesisDropdownOption(
                        'Assign to API Partner',
                        reverse('gdrives:batch-assign-apipartner')),
                    GenesisDropdownOption(
                        'Assign to Rx Partner',
                        reverse('gdrives:batch-assign-rx-partner'))
                ]
            ),
            GenesisAboveTableButton(
                'Assign by CSV',
                reverse('gdrives:assign-by-csv')),
            GenesisAboveTableButton(
                'Build Carton',
                reverse('gdrives:add-warehouse-carton'))
        ]

    def get_page_title(self):
        return 'Manage Available Devices'

    def get_queryset(self):
        return GDrive.objects.filter(status=GDrive.DEVICE_STATUS_AVAILABLE)
available_devices = test(AvailableDeviceTableView.as_view())


class RxPartnerDeviceTableView(GenesisTableView):
    def create_columns(self):
        return [
            AttributeTableColumn('MEID', 'meid'),
            AttributeTableColumn('Serial #', 'device_id'),
            AttributeTableColumn('Rx Partner', 'rx_partner.name'),
            AttributeTableColumn(
                'Device Status',
                'get_status_display',
                searchable=False,
                proxy_field='status'
            ),
            AttributeTableColumn('Carton #', 'warehouse_carton.number'),
            AttributeTableColumn(
                'Date Shipped', 'date_shipped_to_rx_partner'),
            ActionTableColumn(
                'View',
                actions=[
                    ActionItem(
                        'View',
                        GenesisTableLink(
                            'gdrives:detail',
                            url_args=[GenesisTableLinkAttrArg('pk')]
                        )
                    )
                ]
            )
        ]

    def get_above_table_items(self):
        output = []
        if self.get_show_assigned():
            output.append(
                GenesisAboveTableButton(
                    'Show Available',
                    reverse('gdrives:partner-devices')))
        else:
            output.append(
                GenesisAboveTableButton(
                    'Show Assigned',
                    reverse('gdrives:partner-devices') + "?showAssigned=1"))
        return output

    def get_show_assigned(self):
        return bool(self.request.GET.get('showAssigned', False))

    def get_page_title(self):
        return 'Manage Rx Partner Devices'

    def get_queryset(self):
        qs = GDrive.objects.filter(rx_partner__isnull=False)
        if self.get_show_assigned():
            qs = qs.filter(status='assigned')
        else:
            qs = qs.filter(status='available')
        return qs
partner_devices = test(RxPartnerDeviceTableView.as_view())


class NewDeviceTableView(GenesisTableView):
    def create_columns(self):
        return [
            AttributeTableColumn('MEID', 'meid'),
            AttributeTableColumn('Serial #', 'device_id'),
            AttributeTableColumn(
                'MFG Carton #', 'manufacturer_carton.number'),
            AttributeTableColumn('Lot #', 'manufacturer_carton.lot_number'),
            AttributeTableColumn(
                'Last Reading',
                'last_reading.reading_datetime_utc',
                searchable=False,
                sortable=False),
            AttributeTableColumn(
                'Device Status',
                'get_network_status_display',
                searchable=False,
                proxy_field='network_status'
            ),
            ActionTableColumn(
                'View',
                actions=[
                    ActionItem(
                        'View',
                        GenesisTableLink(
                            'gdrives:detail',
                            url_args=[GenesisTableLinkAttrArg('pk')]
                        )
                    )
                ]
            )
        ]

    def get_above_table_items(self):
        return [
            GenesisAboveTableButton(
                'Import Devices', reverse('gdrives:import')),
            GenesisAboveTableButton(
                'Add Device', reverse('gdrives:new'))
        ]

    def get_page_title(self):
        return 'Manage New Devices'

    def get_queryset(self):
        return GDrive.objects.filter(status=GDrive.DEVICE_STATUS_NEW)
new_devices = test(NewDeviceTableView.as_view())


class ReworkedDeviceTableView(GenesisTableView):
    def create_columns(self):
        return [
            AttributeTableColumn('MEID', 'meid'),
            AttributeTableColumn('Serial #', 'device_id'),
            AttributeTableColumn(
                'MFG Carton #', 'manufacturer_carton.number'),
            AttributeTableColumn('Lot #', 'manufacturer_carton.lot_number'),
            AttributeTableColumn(
                'Last Reading',
                'last_reading.reading_datetime_utc',
                searchable=False,
                sortable=False),
            AttributeTableColumn(
                'Device Status',
                'get_network_status_display',
                searchable=False,
                proxy_field='network_status'
            ),
            ActionTableColumn(
                'View',
                actions=[
                    ActionItem(
                        'View',
                        GenesisTableLink(
                            'gdrives:detail',
                            url_args=[GenesisTableLinkAttrArg('pk')]
                        )
                    )
                ]
            )
        ]

    def get_above_table_items(self):
        return [
            GenesisAboveTableDropdown(
                [
                    GenesisDropdownOption(
                        'Inspect Devices',
                        reverse('gdrives:batch-inspect-reworked'))
                ]
            )
        ]

    def get_page_title(self):
        return 'Manage Reworked Devices'

    def get_queryset(self):
        return GDrive.objects.filter(status=GDrive.DEVICE_STATUS_REWORKED)
reworked_devices = test(ReworkedDeviceTableView.as_view())


class NonConformingDeviceTableView(GenesisTableView):
    def create_columns(self):
        return [
            AttributeTableColumn('MEID', 'meid'),
            AttributeTableColumn('Serial #', 'device_id'),
            AttributeTableColumn('Tray #', 'tray_number'),
            AttributeTableColumn('Lot #', 'manufacturer_carton.lot_number'),
            AttributeTableColumn(
                'Non-conformities',
                'get_non_conformity_str',
                proxy_field='non_conformities.non_conformity_types.name'),
            AttributeTableColumn(
                'Status',
                'get_status_display',
                searchable=False,
                proxy_field='status'
            ),
            ActionTableColumn(
                'View',
                actions=[
                    ActionItem(
                        'View',
                        GenesisTableLink(
                            'gdrives:detail',
                            url_args=[GenesisTableLinkAttrArg('pk')]
                        )
                    )
                ]
            )
        ]

    def get_page_title(self):
        return 'Manage Non-Conforming Devices'

    def get_queryset(self):
        return GDrive.objects.filter(status=GDrive.DEVICE_STATUS_REPAIRABLE)
non_conforming_devices = test(NonConformingDeviceTableView.as_view())
