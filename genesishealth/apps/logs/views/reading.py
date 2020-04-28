from datetime import timedelta

from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.timezone import now

from genesishealth.apps.alerts.models import PatientAlertNotificationLogEntry
from genesishealth.apps.api.models import APILogRecord
from genesishealth.apps.gdrives.models import (
    GDriveTransmissionLogEntry, GDriveLogEntry)
from genesishealth.apps.utils.class_views import (
    GenesisTableView, AttributeTableColumn)
from genesishealth.apps.utils.request import admin_user

admin_test = user_passes_test(admin_user)


class LogTableView(GenesisTableView):
    fake_count = True

    def create_columns(self):
        return [
            AttributeTableColumn(
                'Date', 'date_created',
                default_sort=True, default_sort_direction='desc'),
            AttributeTableColumn(
                'Reading Time', 'reading_datetime', searchable=False),
            AttributeTableColumn(
                'Patient',
                'device.get_patient.get_reversed_name',
                sortable=False, searchable=False),
            AttributeTableColumn('Device (MEID)', 'meid', sortable=False),
            AttributeTableColumn(
                'Value', 'glucose_value', sortable=False, searchable=False),
            AttributeTableColumn(
                'Device Exists',
                'device_exists',
                sortable=False,
                searchable=False),
            AttributeTableColumn('Status', 'status', sortable=False),
            AttributeTableColumn(
                'Raw Data', 'raw_data', sortable=False, searchable=False)
        ]

    def get_page_title(self):
        return 'Device Log'

    def get_queryset(self):
        return GDriveLogEntry.objects.filter(
            date_created__gt=now() - timedelta(days=365))
logs = login_required(admin_test(LogTableView.as_view()))


class TransmissionLogTableView(GenesisTableView):
    fake_count = True

    def create_columns(self):
        return [
            AttributeTableColumn(
                'Date', 'datetime',
                default_sort=True,
                default_sort_direction='desc'),
            AttributeTableColumn(
                'Reading Server',
                'reading_server',
                sortable=False),
            AttributeTableColumn(
                'Decrypted Content',
                'decrypted_content',
                sortable=False),
            AttributeTableColumn(
                'Processing Succeeded?',
                'processing_succeeded',
                sortable=False),
            AttributeTableColumn(
                'Success Sent?',
                'success_sent_to_client'),
            AttributeTableColumn(
                'Error',
                'error',
                sortable=False)
        ]

    def get_page_title(self):
        return 'Transmission Log'

    def get_queryset(self):
        return GDriveTransmissionLogEntry.objects.all()
transmission_logs = login_required(
    admin_test(TransmissionLogTableView.as_view()))


class NotificationLogTableView(GenesisTableView):
    fake_count = True

    def create_columns(self):
        return [
            AttributeTableColumn(
                'Date', 'datetime_created',
                default_sort=True,
                default_sort_direction='desc'),
            AttributeTableColumn('Type', 'type'),
            AttributeTableColumn('Recipient', 'recipient'),
            AttributeTableColumn('Patient', 'alert.patient.get_reversed_name'),
            AttributeTableColumn('Success', 'success')
        ]

    def get_page_title(self):
        return 'Notification Log'

    def get_queryset(self):
        return PatientAlertNotificationLogEntry.objects.order_by(
            '-datetime_created').select_related()
notification_logs = login_required(
    admin_test(NotificationLogTableView.as_view()))


class APILogTableView(GenesisTableView):
    fake_count = True

    def create_columns(self):
        return [
            AttributeTableColumn(
                'Time', 'datetime', cell_class='main',
                default_sort=True, default_sort_direction='desc'),
            AttributeTableColumn('Inbound', 'readable_inbound'),
            AttributeTableColumn('URL', 'url'),
            AttributeTableColumn('Call Type', 'readable_api_type'),
            AttributeTableColumn('Data', 'data'),
            AttributeTableColumn('Status', 'readable_status'),
            AttributeTableColumn('Response', 'response')
        ]

    def get_page_title(self):
        return 'API Logs'

    def get_queryset(self):
        return APILogRecord.objects.order_by('-datetime')


api_logs = admin_test(APILogTableView.as_view())
