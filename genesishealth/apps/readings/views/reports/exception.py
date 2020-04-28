import re

from datetime import datetime, timedelta

from django import forms
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils.timezone import get_default_timezone, localtime

from genesishealth.apps.accounts.models import Company, PatientProfile
from genesishealth.apps.utils.class_views.csv_report import (
    CSVReport, CSVReportForm, CSVReportView)
from genesishealth.apps.utils.request import require_admin_permission


class ReadingExceptionReportForm(CSVReportForm):
    company = forms.ModelChoiceField(queryset=Company.objects.all())


class ReadingExceptionReport(CSVReport):
    configuration_form_class = ReadingExceptionReportForm

    def get_filename(self, data):
        cleaned_name = data['company'].name.lower().replace(' ', '_')
        slug_name = re.sub("[^a-z0-9_]", "", cleaned_name)
        return "{0}_{1:%Y_%m_%d}_exception_report.csv".format(
            slug_name, localtime())

    def get_header_rows(self, data):
        header_row = [
            "First Name", "Last Name", "Insurance Identifier", "Group", "DOB",
            "Phone", "Last Reading", "Remaining Readings Today", "Yesterday"
        ]
        # Need to append the previous five days and show the date as the
        # heading
        for i in range(2, 8):
            day = (localtime() - timedelta(days=i)).date()
            header_row.append(day.strftime('%m/%d/%Y'))
        return [header_row]

    def get_item_row(self, patient):
        if patient.patient_profile.date_of_birth is None:
            dob_str = 'N/A'
        else:
            dob_str = patient.patient_profile.date_of_birth.strftime(
                '%m/%d/%Y')
        row = [
            patient.first_name,
            patient.last_name,
            patient.patient_profile.insurance_identifier,
            patient.patient_profile.company.name,
            dob_str,
            patient.patient_profile.contact.phone,
        ]
        tz = get_default_timezone()

        def format_reading(reading):
            return "{0}, {1}".format(
                reading.glucose_value,
                reading.reading_datetime_utc.astimezone(tz).strftime(
                    "%m/%d/%y %I:%M %p"))

        def format_readings(readings):
            readings = [format_reading(reading) for reading in readings]
            return " ; ".join(readings)

        def get_readings_from_n_days_ago(n):
            day = localtime() - timedelta(days=n)
            start = tz.localize(
                datetime(day.year, day.month, day.day))
            end = start + timedelta(days=1)
            return patient.glucose_readings.filter(
                reading_datetime_utc__range=(start, end)).order_by(
                'reading_datetime_utc')

        try:
            last_reading = patient.glucose_readings.order_by(
                '-reading_datetime_utc')[0]
        except IndexError:
            last_reading = None
            row.append('N/A')
        else:
            row.append(format_reading(last_reading))

        # Get readings for today, excluding last reading
        today_readings = get_readings_from_n_days_ago(0)
        # Exclude last reading
        if last_reading is not None:
            today_readings = today_readings.exclude(id=last_reading.id)
        row.append(format_readings(today_readings))
        # Now get readings going back 6 days
        for i in range(1, 7):
            readings = get_readings_from_n_days_ago(i)
            row.append(format_readings(readings))
        return row

    def get_queryset(self, data):
        patients = PatientProfile.objects.filter(company=data['company'])
        patient_ids = []
        tz = get_default_timezone()
        right_now = localtime()
        today_start = tz.localize(
            datetime(right_now.year, right_now.month, right_now.day))
        lower_bound = 60
        upper_bound = 250
        for patient in patients:
            todays_readings = patient.user.glucose_readings.filter(
                reading_datetime_utc__gt=today_start)
            if todays_readings.filter(
                    Q(glucose_value__lt=lower_bound) |
                    Q(glucose_value__gt=upper_bound)).count() > 0:
                patient_ids.append(patient.user.id)
        return User.objects.filter(id__in=patient_ids)


class ReadingExceptionReportView(CSVReportView):
    page_title = "Reading Exception Report"
    report_class = ReadingExceptionReport

    def get_breadcrumbs(self):
        return []


require_admin = require_admin_permission('manage-business-partners')
main = require_admin(ReadingExceptionReportView.as_view())
