import csv

from datetime import datetime, timedelta
from io import BytesIO

from django import forms
from django.contrib.auth import get_user_model
from django.utils.timezone import get_current_timezone, now

from genesishealth.apps.api.models import APIPartner, APILogRecord
from genesishealth.apps.gdrives.models import (
    GDriveLogEntry, GDriveTransmissionLogEntry)
from genesishealth.apps.readings.models import GlucoseReading
from genesishealth.apps.reports.models import TemporaryDownload
from genesishealth.apps.utils.forms import GenesisForm, GenesisBatchForm

import pytz

User = get_user_model()


class BaseDownloadLogForm(GenesisForm):
    start_date = forms.DateField()
    end_date = forms.DateField()

    def clean(self):
        data = self.cleaned_data
        if data['start_date'] >= data['end_date']:
            raise forms.ValidationError(
                'Start date must be before end date.')
        return data

    def clean_end_date(self):
        date = self.cleaned_data['end_date']
        timezone = get_current_timezone()
        dt = timezone.localize(datetime(
            year=date.year, month=date.month, day=date.day
        )).astimezone(pytz.UTC)
        dt += timedelta(days=1, microseconds=-1)
        return dt

    def clean_start_date(self):
        date = self.cleaned_data['start_date']
        timezone = get_current_timezone()
        dt = timezone.localize(datetime(
            year=date.year, month=date.month, day=date.day
        )).astimezone(pytz.UTC)
        return dt


class DownloadGDriveLogForm(BaseDownloadLogForm):
    meid = forms.CharField()

    def get_records(self):
        data = self.cleaned_data
        return GDriveLogEntry.objects.filter(
            meid=data['meid'],
            reading_datetime_utc__range=(
                data['start_date'],
                data['end_date']
            )
        )


class DownloadGDriveTransmissionLogForm(BaseDownloadLogForm):
    meid = forms.CharField()

    def get_records(self):
        data = self.cleaned_data
        return GDriveTransmissionLogEntry.objects.filter(
            meid=data['meid'],
            datetime__range=(
                data['start_date'],
                data['end_date']
            )
        )


class DownloadAPILogForm(BaseDownloadLogForm):
    partner = forms.ModelChoiceField(
        queryset=APIPartner.objects.all(),
        required=False)
    patient_id = forms.CharField(required=False)

    def clean_patient_id(self):
        data = self.cleaned_data
        if data.get('patient_id'):
            try:
                User.objects.filter(patient_profile__isnull=False).get(
                    pk=data['patient_id'])
            except User.DoesNotExist:
                raise forms.ValidationError(
                    'Patient ID does not match a user in the system!')
        return data['patient_id']

    def get_records(self):
        data = self.cleaned_data
        filter_kwargs = {
            'datetime__range': (
                data['start_date'],
                data['end_date'])
        }
        if data.get('partner'):
            filter_kwargs[
                'reading__patient__patient_profile__partners'] = data[
                'partner']
        if data.get('patient_id'):
            filter_kwargs['reading__patient__id'] = data['patient_id']
        return APILogRecord.objects.filter(**filter_kwargs).select_related(
            'reading')


class BatchConvertReadingForm(GenesisBatchForm):
    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester')
        super(BatchConvertReadingForm, self).__init__(*args, **kwargs)

    def save(self):
        for reading_log in self.batch:
            try:
                reading = reading_log.reading
            except GlucoseReading.DoesNotExist:
                continue
            # Convert reading to general.
            reading.measure_type = GlucoseReading.MEASURE_TYPE_NORMAL
            reading.mark_change(self.requester)


class BatchHideReadingForm(GenesisBatchForm):
    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester')
        super(BatchHideReadingForm, self).__init__(*args, **kwargs)

    def save(self):
        for reading_log in self.batch:
            if not getattr(reading_log, self.hide_attribute):
                setattr(reading_log, self.hide_attribute, True)
                reading_log.save()


class BatchHideControlReadingForm(BatchHideReadingForm):
    hide_attribute = 'hide_from_control_log'


class BatchHideQAReadingForm(GenesisBatchForm):
    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester')
        super(BatchHideQAReadingForm, self).__init__(*args, **kwargs)

    def save(self):
        for log_entry in self.batch:
            log_entry.delete()


class BatchHideOrphanedReadingForm(BatchHideReadingForm):
    hide_attribute = 'hide_from_orphaned_log'


class MigrateReadingForm(GenesisBatchForm):
    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester')
        super(MigrateReadingForm, self).__init__(*args, **kwargs)

    def save(self):
        for reading_log in self.batch:
            reading_log.recover()


class AverageReportForm(GenesisForm):
    report_start = forms.DateField()
    report_end = forms.DateField()

    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester')
        super(AverageReportForm, self).__init__(*args, **kwargs)
        self.fields['report_start'].initial = (
            datetime.now() - timedelta(days=89)).date()
        self.fields['report_end'].initial = datetime.now().date()

    def save(self):
        dt_format = '%Y-%m-%d 00:00:00 America/Chicago'
        start = self.cleaned_data['report_start']
        end = self.cleaned_data['report_end']
        start_dts = start.strftime(dt_format)
        end_dts = end.strftime(dt_format)
        total_days = int(
            (end - start).total_seconds() / 60 / 60 / 24) + 1
        query = """
            SELECT
                u.id,
                g.name AS group_name,
                u.first_name,
                u.last_name,
                p.insurance_identifier,
                COUNT(r.id)::real / %s AS average_num_readings
            FROM
                auth_user u
                LEFT JOIN accounts_patientprofile p ON u.id = p.user_id
                LEFT JOIN accounts_genesisgroup g ON g.id = p.group_id
                LEFT JOIN readings_glucosereading r ON (
                    r.patient_id = u.id AND
                    r.reading_datetime_utc AT TIME ZONE 'America/Chicago' BETWEEN %s AND %s)
            WHERE
                u.is_staff = FALSE AND p.user_id IS NOT NULL
            GROUP BY u.id, g.name, u.first_name, u.last_name, p.insurance_identifier"""  # noqa
        qs = User.objects.raw(query, [total_days, start_dts, end_dts])
        date_str = "{} - {}".format(start, end)
        rows = []
        for patient in qs:
            new_row = [
                patient.group_name,
                patient.first_name,
                patient.last_name,
                patient.insurance_identifier,
                round(patient.average_num_readings, 2)
            ]
            rows.append(new_row)

        header_rows = [
            ['Title', 'Patient Daily Average Report'],
            ['Date', date_str],
            ['Group', 'All'],
            ['Number of Patients', len(rows)],
            [],
            ['Group', 'First Name', 'Last Name', 'Insurance Identifier',
             'Readings per Day']
        ]
        output = BytesIO()
        writer = csv.writer(output)
        map(writer.writerow, header_rows + rows)
        content = output.getvalue()
        filename = "{}_daily_average_report.csv".format(now().date())
        self.download = TemporaryDownload.objects.create(
            for_user=self.requester,
            content=content,
            content_type='text/csv',
            filename=filename
        )

    def get_download_id(self):
        if hasattr(self, 'download'):
            return self.download.id
