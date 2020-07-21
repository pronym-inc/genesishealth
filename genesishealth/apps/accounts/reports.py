import csv
import io

from datetime import timedelta
from typing import List, TYPE_CHECKING

from django.contrib.auth.models import User
from django.db.models import Q, QuerySet
from django.utils.timezone import make_naive, now, get_default_timezone

from genesishealth.apps.readings.models import GlucoseReading

if TYPE_CHECKING:
    from genesishealth.apps.accounts.models import PatientProfile
    from genesishealth.apps.gdrives.models import GDriveLogEntry


def _generate_noncompliance_report(qs: 'QuerySet[User]', hours: int, report_name: str, no_pii: bool = False) -> str:
    cutoff = now() - timedelta(hours=hours)
    # Method for finding non-compliant patients.. first find all readings
    # for patients from this group over the specified period.
    # then exclude those patients from the group and use the remainder.
    all_patients = qs
    patient_ids = GlucoseReading.objects.filter(
        gdrive_log_entry__date_created__gte=cutoff, patient__in=all_patients
    ).distinct('patient').values('patient')
    id_list: List[int] = list(map(lambda x: x['patient'], patient_ids))
    non_compliant_patients = all_patients.exclude(id__in=id_list)\
        .prefetch_related('patient_profile')\
        .prefetch_related('patient_profile__last_reading')\
        .prefetch_related('patient_profile__last_reading__gdrive_log_entry')\
        .select_related('patient_profile__contact')\
        .prefetch_related('patient_profile__contact__phone_numbers')\
        .prefetch_related('patient_profile__company')
    rows: List[List[str]] = []
    tz = get_default_timezone()
    patient: User
    for patient in non_compliant_patients:
        last_glucose_value = 'None'
        last_reading_datetime = 'None'
        reading_timestamp = 'None'
        hours_since_last_reading = 'N/A'
        profile: PatientProfile = patient.patient_profile
        if profile.last_reading is not None:
            try:
                profile.last_reading.gdrive_log_entry
            except GDriveLogEntry.DoesNotExist:
                pass
            else:
                dt = profile.last_reading.gdrive_log_entry.date_created
                last_reading_datetime = make_naive(dt, tz).strftime("%m/%d/%y %I:%M:%S %p")
                hours_since_last_reading = str(int(
                    (now() - dt).total_seconds() / 60 / 60 / 24
                ))
            last_glucose_value = str(profile.last_reading.glucose_value)
            reading_timestamp = make_naive(
                profile.last_reading.reading_datetime_utc,
                tz).strftime("%m/%d/%y %I:%M:%S %p")

        if profile.contact.phone_numbers.count() > 0:
            phone = profile.contact.phone_numbers.all()[0].phone
        else:
            phone = 'N/A'
        if no_pii:
            new_row = [
                str(profile.company),
                str(profile.epc_member_identifier),
                str(patient.id)
            ]
        else:
            new_row = [
                str(profile.company),
                str(profile.insurance_identifier),
                f"{patient.last_name}, {patient.first_name}",
                str(profile.date_of_birth),
                str(phone),
            ]
        new_row.extend([
            last_reading_datetime,
            reading_timestamp,
            str(hours_since_last_reading),
            last_glucose_value
        ])
        rows.append(new_row)
    output = io.StringIO()
    writer = csv.writer(output)
    # Write hreaders
    header_rows: List[List[str]] = [
        ['Title', 'Non-Compliance Report'],
        ['Period', '{} - {}'.format(cutoff, now())],
        ['Group', report_name],
        ['Non-Compliant Patients', str(non_compliant_patients.count())],
        [],
    ]
    if no_pii:
        header_rows.append([
            'Group Name',
            'EPC ID',
            'GHT ID',
            'Portal Timestamp (CST)',
            'Reading Timestamp (CST)',
            'Elapsed Hours',
            'Last Reading',
            'Agent',
            'Call Time',
            'Call Type',
            'Call Status',
            'Out of Supplies',
            'Change in Test Freq.',
            'Technical Issues',
            'Travel',
            'Other',
            'Comments/Other'
        ])
    else:
        header_rows.append([
            'Employer',
            'Member ID',
            'Name',
            'Date of Birth',
            'Phone',
            'Portal Timestamp (CST)',
            'Reading Timestamp (CST)',
            'Elapsed Hours',
            'Last Reading',
            'Agent',
            'Call Time',
            'Call Type',
            'Call Status',
            'Out of Supplies',
            'Change in Test Freq.',
            'Technical Issues',
            'Travel',
            'Other',
            'Comments/Other'
        ])
    for hr in header_rows:
        writer.writerow(hr)
    for row in rows:
        writer.writerow(row)
    content = output.getvalue()
    return content


def _generate_target_range_report(qs: 'QuerySet[User]', days: int, report_name: str, no_pii: bool = False) -> str:
    cutoff = now() - timedelta(days=days)
    patients = qs
    readings = GlucoseReading.objects.select_related('patient').\
        prefetch_related('gdrive_log_entry').\
        prefetch_related('patient__patient_profile').\
        select_related('patient__patient_profile__contact').\
        select_related('patient__patient_profile__company').\
        prefetch_related(
            'patient__patient_profile__contact__phone_numbers').\
        filter(gdrive_log_entry__date_created__gte=cutoff,
               patient__in=patients).\
        filter(
            Q(glucose_value__lt=60) | Q(glucose_value__gt=250)
    )
    rows: List[List[str]] = []
    tz = get_default_timezone()
    reading: GlucoseReading
    for reading in readings:
        if reading.patient is None:
            continue
        patient: User = reading.patient
        profile: PatientProfile = patient.patient_profile
        if profile.contact.phone_numbers.all().count() > 0:
            phone = profile.contact.phone_numbers.all()[0].phone
        else:
            phone = 'N/A'

        dt_string = make_naive(
            reading.gdrive_log_entry.date_created, tz).strftime(
                "%m/%d/%y %I:%M:%S %p")
        timestamp_string = make_naive(
            reading.reading_datetime_utc, tz).strftime(
                "%m/%d/%y %I:%M:%S %p")
        if no_pii:
            new_row = [
                str(profile.company),
                str(profile.epc_member_identifier),
                str(patient.id)
            ]
        else:
            new_row = [
                str(profile.company),
                str(profile.insurance_identifier),
                f"{patient.last_name}, {patient.first_name}",
                str(profile.date_of_birth),
                str(phone)
            ]
        new_row.extend([
            dt_string,
            timestamp_string,
            str(reading.glucose_value)
        ])
        rows.append(new_row)
    output = io.StringIO()
    writer = csv.writer(output)
    # Write hreaders
    header_rows: List[List[str]] = [
        ['Title', 'Target Range Report'],
        ['Date', '{} - {}'.format(cutoff, now())],
        ['Group', report_name],
        ['Range Violations', str(readings.count())],
        []
    ]
    if no_pii:
        header_rows.append([
            'Employer',
            'EPC ID',
            'GHT ID',
            'Portal Timestamp (CST)',
            'Reading Timestamp (CST)',
            'Reading',
            'Agent',
            'Call Time',
            'Call Type',
            'Call Status',
            'Medication',
            'Dietary',
            'Illness',
            'Stress',
            'Exercise',
            'Alcohol',
            'Comments/Other'
        ])
    else:
        header_rows.append([
            'Employer',
            'Member ID',
            'Name',
            'Date of Birth',
            'Phone',
            'Portal Timestamp (CST)',
            'Reading Timestamp (CST)',
            'Reading',
            'Agent',
            'Call Time',
            'Call Type',
            'Call Status',
            'Medication',
            'Dietary',
            'Illness',
            'Stress',
            'Exercise',
            'Alcohol',
            'Comments/Other'
        ])
    for hr in header_rows:
        writer.writerow(hr)
    for row in rows:
        writer.writerow(row)
    content = output.getvalue()
    return content
