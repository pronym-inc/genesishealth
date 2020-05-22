import base64
import csv
import io
import json
import logging
import os
import ssl

from datetime import datetime, time, timedelta
from urllib.error import HTTPError, URLError
from urllib.request import urlopen, Request

from dateutil.parser import parse

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.timezone import now

from genesishealth.apps.readings.tasks import forward_reading_to_partner
from genesishealth.apps.utils.func import utcnow

import paramiko

import pytz

logger = logging.getLogger('api')


class APILogRecord(models.Model):
    STATUS_CONNECTION_ERROR = 'connection_error'
    STATUS_JSON_ERROR = 'json_error'
    STATUS_RETURNED_ERROR = 'returned_error'
    STATUS_COMPLETE = 'complete'

    STATUS_CHOICES = (
        (STATUS_CONNECTION_ERROR, 'Failed: Connection Error'),
        (STATUS_RETURNED_ERROR, 'Failed: Remote Server Returned Error'),
        (STATUS_COMPLETE, 'Success')
    )

    API_NAME_REGISTER_DEVICE = 'register_device'
    API_NAME_UNREGISTER_DEVICE = 'unregister_device'
    API_NAME_PUSH_DATA = 'push_data'
    API_NAME_PULL_DATA = 'pull_data'
    API_NAME_CHOICES = (
        (API_NAME_REGISTER_DEVICE, 'Register Device'),
        (API_NAME_UNREGISTER_DEVICE, 'Unregister Device'),
        (API_NAME_PUSH_DATA, 'Push Data'),
        (API_NAME_PULL_DATA, 'Pull Data')
    )

    is_inbound = models.BooleanField()
    datetime = models.DateTimeField()
    url = models.CharField(max_length=255)
    action_type = models.CharField(max_length=255, choices=API_NAME_CHOICES)
    status = models.CharField(max_length=255,
                              choices=STATUS_CHOICES)
    data = models.TextField(null=True)
    response = models.TextField(null=True)
    reading = models.ForeignKey(
        'readings.GlucoseReading', null=True,
        related_name='api_log_records', on_delete=models.SET_NULL)
    for_partner = models.ForeignKey(
        'APIPartner', null=True, related_name='api_log_records', on_delete=models.SET_NULL)

    def readable_api_type(self):
        for k, v in self.API_NAME_CHOICES:
            if self.action_type == k:
                return v
        return 'Unknown'

    def readable_inbound(self):
        return self.is_inbound and 'Inbound' or 'Outbound'

    def readable_status(self):
        for k, v in self.STATUS_CHOICES:
            if self.status == k:
                return v
        return 'Unknown'

    def resolve_reading(self, commit=True):
        from genesishealth.apps.gdrives.models import GDrive
        from genesishealth.apps.readings.models import GlucoseReading
        if self.reading is not None:
            return
        try:
            data = json.loads(self.data)['Glucose']
        except:
            return
        if 'meid' in data:
            try:
                device = GDrive.objects.get(meid=data['meid'])
            except GDrive.DoesNotExist:
                pass
            else:
                if 'readingOn' in data:
                    parsed_dt = parse(data['readingOn'])
                    try:
                        self.reading = device.readings.get(
                            reading_datetime_utc=parsed_dt,
                            glucose_value=data['value'])
                    except GlucoseReading.DoesNotExist:
                        pass
        if self.reading is None and 'patient_id' in data:
            try:
                patient = User.objects.filter(
                    patient_profile__isnull=False).get(pk=data['patient_id'])
            except User.DoesNotExist:
                pass
            else:
                if 'readingOn' in data:
                    parsed_dt = parse(data['readingOn'])
                    try:
                        self.reading = patient.glucose_readings.get(
                            reading_datetime_utc=parsed_dt,
                            glucose_value=data['value'])
                    except GlucoseReading.DoesNotExist:
                        pass
        if commit and self.reading is not None:
            self.save()


class APIFlatfileConnection(models.Model):
    _connection = None

    name = models.CharField(max_length=255, unique=True)
    host = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    delivery_path = models.CharField(max_length=255)
    port = models.PositiveIntegerField(default=22)
    active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name

    def send_file(self, f, name):
        fname = os.path.join(self.delivery_path, name)
        with paramiko.Transport((self.host, self.port)) as transport:
            transport.connect(username=self.username, password=self.password)
            with paramiko.SFTPClient.from_transport(transport) as sftp:
                sftp.putfo(f, fname)


class APIPartner(models.Model):
    API_VERSION_CHOICES = (
        ('1.0', '1.0'),
        ('2.0', '2.0'),
        ('2.1', '2.1')
    )

    name = models.CharField(max_length=255, unique=True)
    short_name = models.CharField(max_length=255, unique=True)
    outgoing_username = models.CharField(max_length=255, blank=True, null=True)
    outgoing_password = models.CharField(max_length=255, blank=True, null=True)
    outgoing_api_key = models.CharField(max_length=255, blank=True, null=True)
    incoming_username = models.CharField(max_length=255, blank=True, null=True)
    incoming_password = models.CharField(max_length=255, blank=True, null=True)
    forward_readings = models.BooleanField()
    send_register_updates = models.BooleanField()
    use_verizon_output_format = models.BooleanField(default=False)
    maximum_send_attempts = models.IntegerField(default=5)
    api_version = models.CharField(
        max_length=255, choices=API_VERSION_CHOICES, default="1.0")
    flatfile_connection = models.ForeignKey(
        'APIFlatfileConnection', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self) -> str:
        return self.name

    def add_patient(self, patient, clear_others=False):
        if clear_others:
            for partner in patient.patient_profile.partners.exclude(
                    pk=self.pk):
                patient.patient_profile.partners.remove(partner)
        # Convert the patient.
        patient.patient_profile.partners.add(self)

    def _do_1_0_reading(self, reading):
        reading_datetime = reading.reading_datetime_utc.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        def check_timezone(tz_name, reading):
            timezone = pytz.timezone(tz_name)
            naive = reading.reading_datetime_utc.replace(tzinfo=None)
            try:
                offset = timezone.utcoffset(naive).total_seconds() / 60 / 60
            except (pytz.NonExistentTimeError, pytz.AmbiguousTimeError):
                return False
            return offset == reading.reading_datetime_offset

        for tz in ('America/New_York', 'America/Chicago',
                   'America/Boise', 'America/Los_Angeles'):
            if check_timezone(tz, reading):
                timezone_name = tz
                break
        else:
            for tz in pytz.common_timezones:
                if check_timezone(tz, reading):
                    timezone_name = tz
                    break
            else:
                timezone_name = "Unknown"

        return {
            'Glucose': {
                'meid': reading.device.meid,
                'value': str(reading.glucose_value),
                'context': reading.measure_type,
                'readingOn': reading_datetime,
                'readingTimeZone': timezone_name
            }
        }

    def _do_2_0_reading(self, reading):
        reading_datetime = reading.reading_datetime_utc.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        def check_timezone(tz_name, reading):
            timezone = pytz.timezone(tz_name)
            naive = reading.reading_datetime_utc.replace(tzinfo=None)
            try:
                offset = timezone.utcoffset(naive).total_seconds() / 60 / 60
            except (pytz.NonExistentTimeError, pytz.AmbiguousTimeError):
                return False
            return offset == reading.reading_datetime_offset
        # Handle offset = 0 as a special case where we
        # look up the patient's timezone and substitute or,
        # failing that, use a default of central time.
        if reading.reading_datetime_offset == 0:
            timezone_name = 'America/Chicago'
        else:
            for tz in ('America/New_York', 'America/Chicago',
                       'America/Boise', 'America/Los_Angeles'):
                if check_timezone(tz, reading):
                    timezone_name = tz
                    break
            else:
                for tz in pytz.common_timezones:
                    if check_timezone(tz, reading):
                        timezone_name = tz
                        break
                else:
                    timezone_name = "Unknown"

        return {
            'Glucose': {
                'patient_id': reading.patient.id,
                'value': str(reading.glucose_value),
                'context': reading.measure_type,
                'readingOn': reading_datetime,
                'readingTimeZone': timezone_name
            }
        }

    def _do_2_1_reading(self, reading):
        reading_data = self._do_2_0_reading(reading)
        reading_data['Glucose'].update({
            'readingOnLocal': reading.reading_datetime.strftime(
                "%Y-%m-%dT%H:%M:%SZ"),
            'readingTimeZoneOffset': reading.reading_datetime_offset,
            'readingId': reading.id,
            'patientID': reading_data['Glucose']['patient_id']
        })
        # Remove old patient ID field.
        del reading_data['Glucose']['patient_id']
        return reading_data

    def forward_patient_readings(self, patient):
        """Forward readings from a patient to the partner."""
        assert self in patient.patient_profile.partners.all()
        if self.forward_readings:
            readings = patient.glucose_readings.all()
            readings.update(commit_attempts=0, committed=False)
            for reading in readings:
                self.send_glucose_reading(reading)

    def generate_reading_data(self, reading):
        """Generates the data that should be sent to remote server."""
        if self.use_verizon_output_format:
            # TO DO
            pass
        elif self.api_version == "1.0":
            return self._do_1_0_reading(reading)
        elif self.api_version == "2.0":
            return self._do_2_0_reading(reading)
        elif self.api_version == "2.1":
            return self._do_2_1_reading(reading)

    def generate_wellness_rows(self, for_date):
        from genesishealth.apps.readings.models import GlucoseReading
        tz = pytz.timezone('America/Chicago')
        start_dt = datetime.combine(for_date, time(tzinfo=tz))
        start_dt = start_dt.astimezone(pytz.UTC)
        end_dt = start_dt + timedelta(days=1) - timedelta(microseconds=1)
        headers = [
            'ClinicID', 'MemberID', 'GroupID', 'DOB', 'FirstName', 'LastName',
            'Gender', 'ScreeningDate', 'VendName', 'SubVendName',
            'RelationToInsured', 'PatientId', 'Ethnicity', 'HispanicLatino',
            'Address1', 'Address2', 'City', 'State', 'PostalCode',
            'EmailAddress', 'PrimaryPhone', 'EmployeeID', 'BP_SYS', 'BP_DIA',
            'HR', 'Ht', 'Wt', 'Waist', 'CHOL', 'HDL', 'TGS', 'GLU', 'LDL',
            'A1c', 'BMI', 'MetabolicSyndrome', 'Fasting', 'Glu_Context',
            'Smoking', 'DIAB_DB', 'Med_HTN', 'Heart_Disease',
            'Kidney_Disease', 'COPD', 'Asthma', 'Pregnant', 'Depression']
        rows = [headers]
        acceptable_measures = [
            GlucoseReading.MEASURE_TYPE_NORMAL,
            GlucoseReading.MEASURE_TYPE_AFTER,
            GlucoseReading.MEASURE_TYPE_BEFORE
        ]
        readings = GlucoseReading.objects.filter(
            patient__patient_profile__in=self.patients.all(),
            reading_datetime_utc__range=(start_dt, end_dt),
            measure_type__in=acceptable_measures).distinct()

        def make_row(reading_or_patient):
            if isinstance(reading_or_patient, GlucoseReading):
                reading = reading_or_patient
                patient = reading.patient
            else:
                patient = reading_or_patient.user
                reading = None
            new_row = []
            profile = patient.patient_profile
            # Clinic ID
            new_row.append("GHT_{:%Y%m%d}".format(for_date))
            # Member ID
            new_row.append(profile.insurance_identifier)
            # Group number
            if (profile.company is not None and
                    profile.company.group_identifier is not None):
                new_row.append(profile.company.group_identifier)
            else:
                new_row.append("")
            # Date of birth
            dob = profile.date_of_birth
            if dob is None:
                new_row.append("")
            else:
                new_row.append("{:%m/%d/%Y}".format(dob))
            # First name, last name
            new_row.extend([patient.first_name, patient.last_name])
            if profile.gender == profile.GENDER_MALE:
                new_row.append('M')
            else:
                new_row.append('F')
            # Day of screening.
            if reading is None:
                new_row.append("{:%m/%d/%Y}".format(now().astimezone(tz)))
            else:
                new_row.append("{:%H:%M:%S %m/%d/%Y}".format(
                    reading.reading_datetime_utc.astimezone(tz)))
            # Name of vendor
            new_row.append('GHT')
            # Now we skip a bunch of rows, but need to have empty values
            new_row.extend([''] * 2)
            # GHT Account No.
            new_row.append(patient.id)
            new_row.extend([''] * 8)
            # Phone
            new_row.append(profile.contact.phone)
            new_row.extend([''] * 10)
            # Reading value
            if reading is None:
                new_row.append('')
            else:
                new_row.append(reading.glucose_value)
            new_row.extend([''] * 5)
            # Context
            if reading is None:
                new_row.append('')
            else:
                context = reading.measure_type
                if context == GlucoseReading.MEASURE_TYPE_NORMAL:
                    context = 'random'
                new_row.append(context)
            new_row.extend([''] * 9)
            return new_row

        for reading in readings:
            rows.append(make_row(reading))
        # Add a row for each patient without a reading.
        absent_patients = self.patients.exclude(
            user__glucose_readings__in=readings)
        for patient in absent_patients:
            rows.append(make_row(patient))
        rows.append(['RowCount: {}'.format(len(rows) - 1)])
        return rows

    def get_queued_attempts(self):
        """Gets all readings that are ready to be sent out."""
        return self.forward_attempts.filter(
            committed=False,
            attempts__lt=self.maximum_send_attempts)

    def get_url(self, type_):
        try:
            return self.locations.get(type=type_).url
        except APILocation.DoesNotExist:
            raise ImproperlyConfigured("Attempting to look up URL for type %s"
                                       " but no such location exists." % type_)

    def make_wellness_document(self, for_date):
        rows = self.generate_wellness_rows(for_date)
        filename = "WellnessData_ght_{:%Y%m%d_%H%M%S}.txt".format(for_date)
        with io.BytesIO() as buf:
            writer = csv.writer(buf, delimiter='|')
            for row in rows:
                writer.writerow(row)
            return (filename, io.BytesIO(buf.getvalue()))

    def queue_and_send_reading(self, reading):
        if settings.SKIP_FORWARD_READINGS:
            return
        try:
            attempt = self.forward_attempts.get(reading=reading)
        except APIReadingForwardAttempt.DoesNotExist:
            attempt = APIReadingForwardAttempt.objects.create(
                partner=self, reading=reading
            )
        self.send_glucose_reading(attempt)

    def remove_patient(self, patient):
        patient.patient_profile.partners.remove(self)

    def send_glucose_reading(self, attempt_or_reading):
        from genesishealth.apps.readings.models import GlucoseReading
        if isinstance(attempt_or_reading, GlucoseReading):
            reading = attempt_or_reading
            attempt, _ = APIReadingForwardAttempt.objects.get_or_create(
                reading=reading, partner=self)
        elif isinstance(attempt_or_reading, APIReadingForwardAttempt):
            attempt = attempt_or_reading
        else:
            raise ValueError("Unknown type for attempt_or_reading")
        if (attempt.committed or
                attempt.attempts >= self.maximum_send_attempts):
            return
        if self not in attempt.reading.patient.patient_profile.partners.all():
            raise Exception('Attempting to send reading to wrong partner.')
        log = APILogRecord(
            is_inbound=False,
            datetime=utcnow(),
            url=self.get_url('push_data'),
            action_type='push_data',
            for_partner=self,
            reading=attempt.reading)
        reading_data = self.generate_reading_data(attempt.reading)
        encoded_data = json.dumps(reading_data)
        log.data = encoded_data
        # Send the reading
        from genesishealth.apps.gdrives.models import \
            GDriveTransmissionLogEntry
        try:
            attempt.reading.log_entry
        except GDriveTransmissionLogEntry.DoesNotExist:
            pass
        else:
            attempt.reading.log_entry.sent_to_api = True
            attempt.reading.log_entry.save()
        attempt.attempts += 1
        push_location = self.get_url('push_data')
        request = Request(push_location)
        if self.api_version == "2.1":
            request.add_header("x-api-key", self.outgoing_api_key)
        base64string = base64.standard_b64encode(
            "%s:%s" % (self.outgoing_username,
                       self.outgoing_password)
        )
        request.add_header("Authorization",
                           "Basic %s" % base64string)
        request.add_header("Content-type",
                           "application/json")
        context = ssl._create_unverified_context()
        try:
            response = urlopen(
                request, encoded_data, 10, context=context)
        except HTTPError as e:
            log.status = 'connection_error'
            log.response = str(e.read())
        except URLError as e:
            log.status = 'connection_error'
            log.response = e.reason
        except Exception as e:
            log.status = 'connection_error'
            log.response = str(e)
        else:
            response_contents = response.read()
            log.response = response_contents
            # Interpret response
            try:
                decoded_response = json.loads(response_contents)
            except ValueError:
                log.status = 'json_error'
            else:
                if decoded_response.get('success'):
                    log.status = 'complete'
                    attempt.committed = True
                    try:
                        attempt.reading.log_entry
                    except GDriveTransmissionLogEntry.DoesNotExist:
                        pass
                    else:
                        attempt.reading.log_entry.received_by_api = True
                        attempt.reading.log_entry.save()
                else:
                    log.status = 'returned_error'
        attempt.save()
        log.save()

    def send_queued_attempts(self):
        """Sends out all queued attempts."""
        for attempt in self.get_queued_attempts():
            forward_reading_to_partner.delay(self.pk, attempt.pk)

    def send_wellness_document(self, for_date):
        filename, doc = self.make_wellness_document(for_date)
        self.flatfile_connection.send_file(doc, filename)


class APIReadingForwardAttempt(models.Model):
    partner = models.ForeignKey(APIPartner, related_name='forward_attempts', on_delete=models.CASCADE)
    reading = models.ForeignKey('readings.GlucoseReading',
                                related_name='forward_attempts', on_delete=models.CASCADE)
    datetime_created = models.DateTimeField(auto_now_add=True)
    committed = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)

    class Meta:
        unique_together = ('partner', 'reading')


class APILocation(models.Model):
    TYPE_CHOICES = (
        ('push_data', 'Push data'),
        ('pull_data', 'Pull data'),
        ('register', 'Register'),
        ('unregister', 'Unregister'),
    )
    partner = models.ForeignKey(APIPartner, related_name="locations", on_delete=models.CASCADE)
    url = models.URLField()
    type = models.CharField(choices=TYPE_CHOICES, max_length=50)

    class Meta:
        unique_together = (('partner', 'type'))


class GenesisAPIException(Exception):
    def __init__(self, message, error_code, *args):
        super(GenesisAPIException, self).__init__(message, *args)
        self.error_code = error_code

    def __str__(self) -> str:
        return '{0} - {1}'.format(self.error_code, self.message)
