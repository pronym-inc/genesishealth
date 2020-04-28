from datetime import timedelta

from dateutil import parser

from django.conf import settings
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count
from django.utils.timezone import now

from genesishealth.apps.api.models import APIPartner
from genesishealth.apps.gdrives.models import (
    GDriveTransmissionLogEntry, GDriveLogEntry)
from genesishealth.apps.logs.forms import (
    BatchConvertReadingForm, BatchHideControlReadingForm,
    BatchHideQAReadingForm, MigrateReadingForm, BatchHideOrphanedReadingForm,
    AverageReportForm)
from genesishealth.apps.logs.models import QALogEntry
from genesishealth.apps.readings.models import GlucoseReading
from genesishealth.apps.reports.views.main import ReportView
from genesishealth.apps.utils.class_views import (
    GenesisTableView, AttributeTableColumn,
    GenesisDropdownOption, GenesisAboveTableDropdown)
from genesishealth.apps.utils.request import admin_user
from genesishealth.apps.utils.views import generic_form


def get_date_range(request):
    start_date = now().date() - timedelta(days=5)
    minimum_start_date = settings.AUDIT_START_DATE
    maximum_end_date = end_date = now().date() + timedelta(days=1)
    if 'start_date' in request.GET:
        try:
            start_date = parser.parse(request.GET['start_date']).date()
        except ValueError:
            pass
        else:
            if start_date < minimum_start_date:
                start_date = minimum_start_date

    if 'end_date' in request.GET:
        try:
            end_date = parser.parse(
                request.GET['end_date']).date() + timedelta(days=1)
        except ValueError:
            pass
        else:
            if end_date > maximum_end_date:
                end_date = maximum_end_date
    return (start_date, end_date)


class SummaryView(ReportView):
    output_format = "html"
    filename = "Summary.pdf"

    def get_context_data(self):
        date_range = get_date_range(self.request)
        log = GDriveTransmissionLogEntry.objects.get_entries_that_should_be_resolved() # noqa
        log = log.filter(datetime__range=date_range)
        data = {r[0]: log.filter(resolution=r[0]).count() for r in GDriveTransmissionLogEntry.RESOLUTION_OPTIONS} # noqa
        # Have to fix some data...
        data[GDriveTransmissionLogEntry.RESOLUTION_VALID] = log.filter(
            resolution=GDriveTransmissionLogEntry.RESOLUTION_VALID,
            associated_patient_profile__demo_patient=False).count()
        data['system_generated'] = log.filter(
            resolution=GDriveTransmissionLogEntry.RESOLUTION_VALID,
            associated_patient_profile__demo_patient=True).count()
        data['total'] = log.count()
        data['valid_patient_subtotal'] = (
            data[GDriveTransmissionLogEntry.RESOLUTION_VALID] +
            data['system_generated'])
        fields = (
            GDriveTransmissionLogEntry.RESOLUTION_VALID,
            GDriveTransmissionLogEntry.RESOLUTION_NO_PATIENT,
            GDriveTransmissionLogEntry.RESOLUTION_UNKNOWN_DEVICE,
            GDriveTransmissionLogEntry.RESOLUTION_INVALID_MEASURE,
            'system_generated')
        data['valid_subtotal'] = sum(map(lambda x: data[x], fields))
        data['invalid_subtotal'] = data['invalid'] + data['duplicate']
        data['failed_subtotal'] = (
            data['processing_failed'] + data['unresolved'])
        return {'data': data, 'start_date': date_range[0],
                'end_date': date_range[1] - timedelta(days=1)}
audit_summary = SummaryView.as_view()


class APIReportView(ReportView):
    output_format = "html"
    filename = "API.pdf"

    def get_context_data(self):
        date_range = get_date_range(self.request)
        log = GDriveTransmissionLogEntry.objects.get_entries_that_should_be_resolved() # noqa
        log = log.filter(datetime__range=date_range)
        data = []
        for partner in APIPartner.objects.all():
            partner_log = log.filter(
                associated_patient_profile__partners=partner)
            data.append({
                'name': partner.name,
                'expected': partner_log.count(),
                'sent': partner_log.filter(sent_to_api=True).count(),
                'success': partner_log.filter(
                    sent_to_api=True, received_by_api=True).count(),
                'errors': partner_log.filter(
                    sent_to_api=True, received_by_api=False).count(),
            })
        total = sum(map(lambda x: x['expected'], data))
        return {'data': data, 'total': total, 'start_date': date_range[0],
                'end_date': date_range[1] - timedelta(days=1)}
audit_api = APIReportView.as_view()


class ControlReportView(ReportView):
    output_format = "html"
    filename = "Control Report.pdf"

    def get_context_data(self):
        date_range = get_date_range(self.request)
        data = GlucoseReading.objects.filter(
            measure_type=GlucoseReading.MEASURE_TYPE_TEST,
            reading_datetime_utc__range=date_range).\
            values('device__meid').\
            annotate(count=Count('device__meid')).order_by('count')
        return {'data': data,
                'start_date': date_range[0],
                'end_date': date_range[1] - timedelta(days=1)}
audit_control_report = ControlReportView.as_view()


class ControlLogTableView(GenesisTableView):
    def create_columns(self):
        return [
            AttributeTableColumn(
                'Date',
                'date_created',
                default_sort_direction='desc',
                default_sort=True
            ),
            AttributeTableColumn('Reading Time', 'reading_datetime'),
            AttributeTableColumn(
                'Patient', 'device.get_patient.get_reversed_name'),
            AttributeTableColumn('Device (MEID)', 'meid'),
            AttributeTableColumn('Value', 'glucose_value'),
            AttributeTableColumn('Device Exists', 'device_exists'),
            AttributeTableColumn('Status', 'status'),
            AttributeTableColumn('Raw Data', 'raw_data')
        ]

    def get_above_table_items(self):
        return [
            GenesisAboveTableDropdown([
                GenesisDropdownOption(
                    'Convert and Migrate to Patient',
                    reverse('logs:audit-control-log-convert')
                ),
                GenesisDropdownOption(
                    'Hide From Log',
                    reverse('logs:audit-control-log-hide')
                )
            ])
        ]

    def get_page_title(self):
        return 'Control Test Log'

    def get_queryset(self):
        return GDriveLogEntry.objects.filter(
            reading__measure_type=GlucoseReading.MEASURE_TYPE_TEST,
            hide_from_control_log=False
        ).order_by('-date_created')
audit_control_log = ControlLogTableView.as_view()


@login_required
@user_passes_test(admin_user)
def audit_control_log_convert(request):
    return generic_form(
        request,
        form_class=BatchConvertReadingForm,
        page_title="Convert Readings",
        system_message="The readings have been converted.",
        batch=True,
        go_back_until=['audit-control-log'],
        only_batch_input=True,
        batch_queryset=GDriveLogEntry.objects.filter(
            hide_from_control_log=False,
            reading__measure_type=GlucoseReading.MEASURE_TYPE_TEST),
        form_kwargs={'requester': request.user}
    )


@login_required
@user_passes_test(admin_user)
def audit_control_log_hide(request):
    return generic_form(
        request,
        form_class=BatchHideControlReadingForm,
        page_title="Hide Readings",
        system_message="The readings have been hidden.",
        batch=True,
        go_back_until=['audit-control-log'],
        only_batch_input=True,
        batch_queryset=GDriveLogEntry.objects.filter(
            hide_from_control_log=False,
            reading__measure_type=GlucoseReading.MEASURE_TYPE_TEST),
        form_kwargs={'requester': request.user}
    )


class QATableView(GenesisTableView):
    def create_columns(self):
        return [
            AttributeTableColumn(
                'Date',
                'datetime_created',
                default_sort=True,
                default_sort_direction='desc'),
            AttributeTableColumn('Reading Datetime', 'reading_datetime'),
            AttributeTableColumn('Device (MEID)', 'meid'),
            AttributeTableColumn('Value', 'glucose_value')
        ]

    def get_above_table_items(self):
        return [
            GenesisAboveTableDropdown([
                GenesisDropdownOption(
                    'Hide From Log', reverse('logs:audit-qa-hide'))
            ])
        ]

    def get_page_title(self):
        return 'QA Log'

    def get_queryset(self):
        start_date, end_date = get_date_range(self.request)
        return QALogEntry.objects.filter(
            datetime_created__range=(start_date, end_date))
audit_qa = QATableView.as_view()


@login_required
@user_passes_test(admin_user)
def audit_qa_hide(request):
    return generic_form(
        request,
        form_class=BatchHideQAReadingForm,
        page_title="Hide Readings",
        system_message="The readings have been hidden.",
        batch=True,
        go_back_until=['audit-qa'],
        only_batch_input=True,
        batch_queryset=QALogEntry.objects.all(),
        form_kwargs={'requester': request.user}
    )


class OrphanedTableView(GenesisTableView):
    def create_columns(self):
        return [
            AttributeTableColumn(
                'Date',
                'datetime_created',
                default_sort=True,
                default_sort_direction='desc'),
            AttributeTableColumn('Device (MEID)', 'get_meid'),
            AttributeTableColumn('Value', 'get_glucose_value'),
            AttributeTableColumn('Raw Data', 'decrypted_content'),
            AttributeTableColumn('Status', 'get_resolution_display')
        ]

    def get_above_table_items(self):
        return [
            GenesisAboveTableDropdown([
                GenesisDropdownOption(
                    'Migrate Readings', reverse('logs:audit-orphaned-convert')
                ),
                GenesisDropdownOption(
                    'Hide From Log', reverse('logs:audit-orphaned-hide')
                )
            ])
        ]

    def get_page_title(self):
        return 'Orphaned Reading Log'

    def get_queryset(self):
        return GDriveTransmissionLogEntry.objects.filter(
            resolution=GDriveTransmissionLogEntry.RESOLUTION_NO_PATIENT,
            hide_from_orphaned_log=False
        ).order_by('-datetime')
audit_orphaned = OrphanedTableView.as_view()


@login_required
@user_passes_test(admin_user)
def audit_orphaned_convert(request):
    queryset = GDriveTransmissionLogEntry.objects.filter(
        resolution=GDriveTransmissionLogEntry.RESOLUTION_NO_PATIENT,
        hide_from_orphaned_log=False)
    return generic_form(
        request,
        form_class=MigrateReadingForm,
        page_title="Convert Readings",
        system_message="The readings have been migrated.",
        batch=True,
        go_back_until=['audit-control-log'],
        only_batch_input=True,
        batch_queryset=queryset,
        form_kwargs={'requester': request.user}
    )


@login_required
@user_passes_test(admin_user)
def audit_orphaned_hide(request):
    return generic_form(
        request,
        form_class=BatchHideOrphanedReadingForm,
        page_title="Hide Readings",
        system_message="The readings have been hidden.",
        batch=True,
        go_back_until=['audit-qa'],
        only_batch_input=True,
        batch_queryset=GDriveTransmissionLogEntry.objects.filter(
            resolution=GDriveTransmissionLogEntry.RESOLUTION_NO_PATIENT,
            hide_from_orphaned_log=False),
        form_kwargs={'requester': request.user}
    )


@login_required
@user_passes_test(admin_user)
def audit_average(request):
    return generic_form(
        request,
        form_class=AverageReportForm,
        form_kwargs={'requester': request.user},
        page_title='Generate Daily Average Report',
        system_message='Your report has been generated.',
        send_download_url=True)
