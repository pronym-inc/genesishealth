from datetime import timedelta

from django.urls import reverse
from django.db.models import Q
from django.utils.timezone import now

from genesishealth.apps.accounts.models import PatientProfile
from genesishealth.apps.gdrives.forms import UpdateCellularStatusForm
from genesishealth.apps.gdrives.models import GDrive
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.class_views import (
    GenesisAboveTableButton, GenesisDetailView, GenesisBaseDetailPane)
from genesishealth.apps.utils.class_views.form import GenesisFormView
from genesishealth.apps.utils.class_views.table import (
    GenesisTableView, AttributeTableColumn)
from genesishealth.apps.utils.class_views.csv_report import (
    CSVReport, CSVReportView)
from genesishealth.apps.utils.request import require_admin_permission


require_cell_test = require_admin_permission('cellular-management')


class ActiveMetersPane(GenesisBaseDetailPane):
    template_name = 'gdrives/cellular/detail_panes/active.html'
    pane_title = "Active Meters"


class RecentDeactivationsPane(GenesisBaseDetailPane):
    template_name = 'gdrives/cellular/detail_panes/recent_deactivations.html'
    pane_title = "Recent Deactivations"


class NewDevicesPane(GenesisBaseDetailPane):
    template_name = 'gdrives/cellular/detail_panes/new.html'
    pane_title = "New Devices Awaiting Activation"


class CellularManagementView(GenesisDetailView):
    pane_classes = (
        ActiveMetersPane, RecentDeactivationsPane, NewDevicesPane)
    page_title = "Cellular Management"

    def get_buttons(self):
        return [
            GenesisAboveTableButton(
                'Update Network Status',
                reverse('gdrives:cellular-update-status')),
            GenesisAboveTableButton(
                'Full MEID List',
                reverse('gdrives:cellular-meid-list')),
            GenesisAboveTableButton(
                'Meter Deactivation Report',
                reverse('gdrives:cellular-deactivation-report'))
        ]


cellular_index = require_cell_test(CellularManagementView.as_view())


class UpdateCellularStatusFormView(GenesisFormView):
    form_class = UpdateCellularStatusForm
    page_title = "Update Cellular Status"
    success_message = "The devices have been updated."
    go_back_until = ["gdrives:cellular-management"]


update_cellular_status = require_cell_test(
    UpdateCellularStatusFormView.as_view())


class CellularMEIDListView(GenesisTableView):
    page_title = "MEID List"

    def create_columns(self):
        return [
            AttributeTableColumn('MEID', 'meid'),
            AttributeTableColumn('MPN', 'phone_number'),
            AttributeTableColumn(
                'Date/Time Network Service Activated',
                'datetime_network_status_activated'),
            AttributeTableColumn(
                'Network Status', 'get_network_status_display'),
            AttributeTableColumn(
                'Date/Time Network Status Changed',
                'datetime_network_status_changed')
        ]

    def get_above_table_items(self):
        return [
            GenesisAboveTableButton(
                'Export',
                reverse('gdrives:cellular-meid-list-csv'))
        ]

    def get_breadcrumbs(self):
        return [
            Breadcrumb(
                'Cellular Management',
                reverse('gdrives:cellular-management'))
        ]

    def get_queryset(self):
        return GDrive.objects.all()


cellular_meid_list = require_cell_test(
    CellularMEIDListView.as_view())


class CellularFullMEIDListReport(CSVReport):
    header_rows = [[
        'MEID', 'MPN', 'Serial #', 'IP', 'Datetime Activated',
        'Network Status', 'Status Changed'
    ]]

    def get_filename(self, data):
        return "meid_list.csv"

    def get_item_row(self, gdrive):
        return [
            gdrive.meid,
            gdrive.phone_number,
            gdrive.device_id,
            gdrive.ip_address,
            gdrive.datetime_network_status_activated.date() if
            gdrive.datetime_network_status_activated else
            "N/A",
            gdrive.network_status,
            gdrive.datetime_network_status_changed.date() if
            gdrive.datetime_network_status_changed else
            "N/A"
        ]

    def get_queryset(self, data):
        return GDrive.objects.all()


class CellularFullMEIDListReportView(CSVReportView):
    page_title = "Full MEID Export"
    report_class = CellularFullMEIDListReport

    def get_breadcrumbs(self):
        return [
            Breadcrumb(
                'Cellular Management',
                reverse('gdrives:cellular-management')),
            Breadcrumb(
                'MEID List',
                reverse('gdrives:cellular-meid-list')),
        ]


cellular_meid_list_csv = require_cell_test(
    CellularFullMEIDListReportView.as_view())


def get_deactivate_devices():
    cutoff_dt = now() - timedelta(days=60)
    return GDrive.objects.filter(
        group__skip_device_deactivation=False,
        network_status=GDrive.DEVICE_NETWORK_STATUS_ACTIVE
    ).filter(
        Q(patient__isnull=True, datetime_replaced__lt=cutoff_dt) |
        Q(
            patient__patient_profile__account_status=PatientProfile.ACCOUNT_STATUS_TERMED  # noqa
        )
    )


class CellularDeactivationListView(GenesisTableView):
    page_title = "Meter Deactivation List"

    def create_columns(self):
        return [
            AttributeTableColumn('MEID', 'meid'),
            AttributeTableColumn('MPN', 'phone_number'),
            AttributeTableColumn(
                'Patient Name', 'get_patient.get_reversed_name'),
            AttributeTableColumn(
                'Patient Status',
                'get_patient.patient_profile.get_account_status_display'),
            AttributeTableColumn(
                'Device Status', 'get_status_display'),
            AttributeTableColumn(
                'Network Status', 'get_network_status_display')
        ]

    def get_above_table_items(self):
        return [
            GenesisAboveTableButton(
                'Export',
                reverse('gdrives:cellular-deactivation-report-csv'))
        ]

    def get_breadcrumbs(self):
        return [
            Breadcrumb(
                'Cellular Management',
                reverse('gdrives:cellular-management'))
        ]

    def get_queryset(self):
        return get_deactivate_devices()
cellular_deactivation_report = require_cell_test(
    CellularDeactivationListView.as_view())


class CellularDeactivationReport(CSVReport):
    header_rows = [[
        'MEID', 'MPN', 'Patient Name', 'GHT ID',
        'Patient Status', 'Patient Group', 'TPA/Payor', 'Device Status',
        'Datetime Activated', 'Network Status', 'Status Changed',
        'Datetime Replaced'
    ]]

    def get_filename(self, data):
        return "deactivation_list.csv"

    def get_item_row(self, gdrive):
        patient = gdrive.patient
        prof = company = payor = None
        if patient is None and gdrive.last_assigned_patient is not None:
            patient = gdrive.last_assigned_patient
        if patient is not None:
            prof = patient.patient_profile
            company = prof.company
            if company.payor:
                payor = company.payor
        return [
            gdrive.meid,
            gdrive.phone_number,
            patient.get_reversed_name() if patient is not None else "N/A",
            patient.id if patient is not None else "N/A",
            prof.account_status if prof is not None else "N/A",
            company.name if company is not None else "N/A",
            payor.name if payor is not None else "N/A",
            "Assigned" if patient is not None else "Unassigned",
            (gdrive.datetime_network_status_activated.date() if
                gdrive.datetime_network_status_activated else
                "N/A"),
            gdrive.network_status,
            (gdrive.datetime_network_status_changed.date() if
                gdrive.datetime_network_status_changed else
                "N/A"),
            (gdrive.datetime_replaced.date() if
                gdrive.datetime_replaced is not None else
                "N/A")
        ]

    def get_queryset(self, data):
        return get_deactivate_devices()


class CellularDeactivationReportView(CSVReportView):
    page_title = "Cellular Deactivation Report"
    report_class = CellularDeactivationReport

    def get_breadcrumbs(self):
        return [
            Breadcrumb(
                'Cellular Management',
                reverse('gdrives:cellular-management')),
            Breadcrumb(
                'Deactivation List',
                reverse('gdrives:cellular-deactivation-report-csv')),
        ]
cellular_deactivation_report_csv = require_cell_test(
    CellularDeactivationReportView.as_view())
