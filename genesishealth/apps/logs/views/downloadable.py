import csv
import io

from datetime import datetime

from django.template.loader import get_template
from django.utils.timezone import get_current_timezone
from django.views.generic import TemplateView
from django.views.generic.edit import FormMixin

from genesishealth.apps.accounts.models import PatientProfile
from genesishealth.apps.gdrives.models import GDrive
from genesishealth.apps.logs.forms import (
    DownloadGDriveLogForm, DownloadGDriveTransmissionLogForm,
    DownloadAPILogForm)
from genesishealth.apps.reports.models import TemporaryDownload
from genesishealth.apps.utils.class_views import (
    GenesisTableView, AttributeTableColumn, GenesisAboveTableRaw)
from genesishealth.apps.utils.func import get_attribute_extended
from genesishealth.apps.utils.request import genesis_redirect


class LogIndexView(TemplateView):
    template_name = 'logs/index.html'


class BaseDownloadLogEntryView(FormMixin, GenesisTableView):
    force_batch = True
    additional_js_templates = ['logs/select_meid.js']

    def create_columns(self):
        return [
            AttributeTableColumn('MEID', 'meid'),
            AttributeTableColumn('Serial #', 'device_id'),
            AttributeTableColumn('Patient', 'patient.get_full_name'),
            AttributeTableColumn(
                'Last Reading',
                'patient.patient_profile.last_reading.reading_datetime_utc')
        ]

    def form_valid(self, form):
        records = form.get_records()
        b = io.BytesIO()
        writer = csv.writer(b)
        # Write in headers.
        data = form.cleaned_data
        writer.writerow(['Title', self.report_title])
        writer.writerow(['Date', '{} - {}'.format(
            data['start_date'].astimezone(get_current_timezone()),
            data['end_date'].astimezone(get_current_timezone()))])
        for header_row in self.get_search_description_rows(form):
            writer.writerow(header_row)
        # Empty buffer row
        writer.writerow([])
        # Column headers.
        writer.writerow(self.headers)
        for record in records:
            row = []
            for column_name in self.column_names:
                val = get_attribute_extended(record, column_name)
                # If it's a datetime, convert to server
                # local time.
                if isinstance(val, datetime):
                    val = val.astimezone(get_current_timezone())
                row.append(val)
            writer.writerow(row)
        content = b.getvalue()
        dl = TemporaryDownload.objects.create(
            for_user=self.request.user,
            content=content,
            content_type='text/csv',
            filename=self.get_report_filename()
        )
        return genesis_redirect(
            self.request, None, then_download_id=dl.id)

    def get_above_table_items(self):
        form = self.get_form()
        template = get_template('logs/base_log.html')
        content = template.render({'form': form}, self.request)
        return [
            GenesisAboveTableRaw(content)
        ]

    def get_page_title(self):
        return self.report_title

    def get_queryset(self):
        return GDrive.objects.all()

    def get_report_filename(self):
        return self.csv_filename

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class DownloadGDriveLogEntryView(BaseDownloadLogEntryView):
    csv_filename = 'gdrive_log.csv'
    report_title = "GDrive Log Report"
    form_class = DownloadGDriveLogForm
    column_names = [
        'date_created',
        'reading_datetime_utc',
        'reading.patient.id',
        'meid',
        'reading.glucose_value',
        'status',
        'successful',
    ]
    headers = [
        'Reading Received Datetime',
        'Reading Device Timestamp',
        'Account No.',
        'MEID',
        'Glucose Value',
        'Status',
        'Successful?'
    ]

    def get_search_description_rows(self, form):
        data = form.cleaned_data
        return [['MEID', data['meid']]]


class DownloadGDriveTransmissionLogEntryView(BaseDownloadLogEntryView):
    csv_filename = 'transmission_log.csv'
    report_title = "GDrive Transmission Log Report"
    form_class = DownloadGDriveTransmissionLogForm
    column_names = [
        'datetime',
        'reading.reading_datetime_utc',
        'reading.patient.id',
        'meid',
        'reading.glucose_value',
        'sent_to_api',
        'received_by_api'
    ]
    headers = [
        'Reading Received Datetime',
        'Reading Device Timestamp',
        'Account No.',
        'MEID',
        'Glucose Value',
        'Sent to API?',
        'Received by API?'
    ]

    def get_search_description_rows(self, form):
        data = form.cleaned_data
        return [['MEID', data['meid']]]


class DownloadAPILogEntryView(BaseDownloadLogEntryView):
    csv_filename = 'api_log.csv'
    report_title = "API Log Report"
    form_class = DownloadAPILogForm
    column_names = [
        'datetime',
        'reading.reading_datetime_utc',
        'reading.patient.id',
        'reading.device.meid',
        'reading.glucose_value',
        'status',
        'data',
        'response'
    ]
    headers = [
        'Reading Received Datetime',
        'Reading Device Timestamp',
        'Account No.',
        'MEID',
        'Glucose Value',
        'API Status',
        'Data Sent',
        'Response Received'
    ]
    additional_js_templates = ['logs/select_patient.js']

    def create_columns(self):
        return [
            AttributeTableColumn('GHT Account No', 'id'),
            AttributeTableColumn('Patient', 'get_full_name'),
            AttributeTableColumn(
                'Last Reading',
                'patient_profile.last_reading.reading_datetime_utc')
        ]

    def get_search_description_rows(self, form):
        data = form.cleaned_data
        output = []
        if data.get('partner'):
            output.append(['Partner', data['partner'].name])
        if data.get('patient_id'):
            output.append(['Account No.', data['patient_id']])
        return output

    def get_queryset(self):
        return PatientProfile.myghr_patients.get_users()
