import os
import sys


sys.path.append("/webapps/genesishealth/src/genesishealth")
os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE', 'genesishealth.conf.settings')

import django  # noqa

django.setup()

import csv

from dateutil.parser import parse
from io import BytesIO

from django.contrib.auth.models import User
from django.db.models import DurationField, ExpressionWrapper, F
from django.utils.timezone import get_default_timezone

from genesishealth.apps.accounts.models import Company
from genesishealth.apps.readings.models import GlucoseReading
from genesishealth.apps.reports.models import TemporaryDownload


def generate_reading_delay_report(datetime_start, datetime_end, companies):
    expression = ExpressionWrapper(
        F('gdrive_log_entry__date_created') - F('reading_datetime_utc'),
        DurationField()
    )
    qs = GlucoseReading.objects.filter(
        reading_datetime_utc__range=(datetime_start, datetime_end),
        patient__patient_profile__company__in=companies).annotate(
        lag_time=expression)
    rows = [[
        'Company',
        'GHT ID',
        'Insurance ID',
        'Glucose Value',
        'Device Timestamp',
        'Server Timestamp (Received)',
        'Lag Time',
        'Bucket'
    ]]
    for reading in qs:
        patient = reading.patient
        profile = patient.patient_profile

        lag_days = reading.lag_time.days
        lag_hours = reading.lag_time.seconds / 60 / 60
        lag_minutes = reading.lag_time.seconds % 3600 / 60
        lag_seconds = reading.lag_time.seconds % 60

        if lag_days > 0:
            lag_string = "{0} {1}:{2}:{3}".format(
                lag_days,
                lag_hours,
                lag_minutes,
                lag_seconds
            )
        else:
            lag_string = "{0}:{1}:{2}".format(
                lag_hours,
                lag_minutes,
                lag_seconds
            )

        if lag_days > 0:
            bucket = '> 24h'
        elif reading.lag_time.seconds > (60 * 60):
            bucket = '1h - 24h'
        elif reading.lag_time.seconds > (60 * 5):
            bucket = '5m - 60m'
        elif reading.lag_time.seconds > (60 * 3):
            bucket = '3m - 5m'
        elif reading.lag_time.seconds > 60:
            bucket = '1m - 3m'
        else:
            bucket = '< 1m'

        rows.append([
            profile.company.name,
            patient.id,
            profile.insurance_identifier,
            reading.glucose_value,
            reading.reading_datetime_utc,
            reading.gdrive_log_entry.date_created,
            lag_string,
            bucket
        ])
    return rows


tz = get_default_timezone()
start_dt = tz.localize(parse(sys.argv[1]))
end_dt = tz.localize(parse(sys.argv[2]))
companies = Company.objects.filter(id__in=(89, 158, 159))
rows = generate_reading_delay_report(start_dt, end_dt, companies)
buf = BytesIO()
writer = csv.writer(buf)
for row in rows:
    writer.writerow(row)
buf.seek(0)
filename = "{0}_reading_lag_report.csv".format(
    start_dt.strftime("%Y_%m_%d"))
recipient = User.objects.get(pk=sys.argv[3])
TemporaryDownload.objects.create(
    for_user=recipient,
    content=buf.getvalue(),
    filename=filename)
