import logging
import json
import datetime
import pytz

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.utils.timezone import now

from genesishealth.apps.api.models import APIPartner
from genesishealth.apps.dropdowns.models import DeviceProblem, MeterDisposition
from genesishealth.apps.utils.func import utcnow


logger = logging.getLogger('gdrives')


class GDriveManager(models.Manager):
    def create_device(self, *args, **kwargs):
        device = self.model(*args, **kwargs)
        device.save()

        return device

    def get_available_devices(self):
        return self.get_live_devices().filter(
            patient__isnull=True,
            assigned_at__isnull=True,
            demo=False,
        )

    def get_assigned_devices(self):
        return self.get_live_devices().filter(
            patient__isnull=False,
            assigned_at__isnull=False,
            demo=False,
        )

    def get_live_devices(self):
        """Hide various undesirables."""
        return self.get_queryset().filter(
            is_verizon_monitoring_device=False,
            is_scalability_device=False,
            is_verizon_testing_device=False)

    def get_verizon_utility_devices(self):
        """Gets all Verizon testing/monitoring devices."""
        return self.get_query_set().filter(
            Q(is_verizon_monitoring_device=True) |
            Q(is_scalability_device=True) |
            Q(is_verizon_testing_device=True))


class GDrive(models.Model):
    DEVICE_STATUS_NEW = 'new'
    DEVICE_STATUS_AVAILABLE = 'available'
    DEVICE_STATUS_ASSIGNED = 'assigned'
    DEVICE_STATUS_UNASSIGNED = 'unassigned'
    DEVICE_STATUS_REPAIRABLE = 'repairable'
    DEVICE_STATUS_REWORKED = 'reworked'
    DEVICE_STATUS_RETURNED = 'returned'
    DEVICE_STATUS_DEMO = 'demo'
    DEVICE_STATUS_FAILED_DELIVERY = 'failed delivery'

    DEVICE_STATUS_CHOICES = (
        (DEVICE_STATUS_NEW, 'New'),
        (DEVICE_STATUS_AVAILABLE, 'Available'),
        (DEVICE_STATUS_ASSIGNED, 'Assigned'),
        (DEVICE_STATUS_UNASSIGNED, 'Unassigned'),
        (DEVICE_STATUS_REPAIRABLE, 'Repairable'),
        (DEVICE_STATUS_REWORKED, 'Reworked'),
        (DEVICE_STATUS_RETURNED, 'Returned'),
        (DEVICE_STATUS_DEMO, 'Demo'),
        (DEVICE_STATUS_FAILED_DELIVERY, 'Failed Delivery')
    )

    DEVICE_NETWORK_STATUS_DEACTIVATED = 'deactivated'
    DEVICE_NETWORK_STATUS_LOADED = 'loaded'
    DEVICE_NETWORK_STATUS_ACTIVE = 'active'
    DEVICE_NETWORK_STATUS_SUSPENDED = 'suspended'

    DEVICE_NETWORK_STATUS_CHOICES = (
        (DEVICE_NETWORK_STATUS_DEACTIVATED, 'Deactivated'),
        (DEVICE_NETWORK_STATUS_LOADED, 'Loaded'),
        (DEVICE_NETWORK_STATUS_ACTIVE, 'Active'),
        (DEVICE_NETWORK_STATUS_SUSPENDED, 'Suspended')
    )

    patient = models.ForeignKey(User, models.SET_NULL, blank=True, null=True,
                                related_name='gdrives')
    unassigned_patients = models.ManyToManyField(
        User, related_name='previous_devices')
    verizon_patient = models.ForeignKey(
        User, models.SET_NULL, blank=True, null=True, editable=False,
        related_name="verizon_devices")
    last_assigned_patient = models.ForeignKey(
        User, models.SET_NULL,
        blank=True, null=True, editable=False, related_name="+")
    group = models.ForeignKey(
        'accounts.GenesisGroup', models.SET_NULL,
        blank=True, null=True, related_name='gdrives')
    professional = models.ForeignKey(
        User, models.SET_NULL,
        blank=True, null=True, related_name="child_gdrives",
        limit_choices_to={'groups__name': 'Professional'}
    )
    meid = models.CharField(max_length=16, unique=True)
    device_type = models.CharField(blank=True, max_length=100,
                                   default="glucose")
    device_id = models.CharField(
        max_length=100, unique=True, verbose_name='Serial number')
    created_at = models.DateTimeField(auto_now_add=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    verizon_update_attempts = models.IntegerField(blank=True, default=0)
    partner = models.ForeignKey(
        APIPartner, models.SET_NULL, null=True, related_name="gdrives")
    # This indicates whether a device is used by the demo system.
    # See genesishealth.apps.accounts.models.DemoPatientProfile
    demo = models.BooleanField(default=False)
    # This indicates whether the device is used for testing with Verizon
    is_verizon_testing_device = models.BooleanField(default=False)
    # This indicates whether the device is used for monitoring with Verizon
    is_verizon_monitoring_device = models.BooleanField(default=False)
    # Indicates whether a device is being used for scalability.
    is_scalability_device = models.BooleanField(default=False)
    last_reading = models.ForeignKey(
        'readings.GlucoseReading', null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(
        blank=True, editable=False, max_length=255,
        choices=DEVICE_STATUS_CHOICES, default=DEVICE_STATUS_NEW)
    lot_number = models.CharField(max_length=255)
    manufacturer_carton = models.ForeignKey(
        'GDriveManufacturerCarton', related_name='devices', null=True,
        verbose_name='Mfg. carton', on_delete=models.SET_NULL)
    warehouse_carton = models.ForeignKey(
        'GDriveWarehouseCarton', related_name='devices', null=True,
        verbose_name='Warehouse carton', on_delete=models.SET_NULL)
    tray_number = models.CharField(max_length=255, null=True)
    datetime_failed_delivery = models.DateTimeField(null=True)
    datetime_activated = models.DateTimeField(null=True)
    datetime_status_changed = models.DateTimeField(null=True)
    datetime_inspected = models.DateTimeField(null=True)
    datetime_assigned = models.DateTimeField(null=True)
    datetime_replaced = models.DateTimeField(null=True)
    datetime_reworked = models.DateTimeField(null=True)

    phone_number = models.CharField(max_length=255, blank=True)
    ip_address = models.CharField(max_length=255, blank=True)
    network_status = models.CharField(
        max_length=255,
        choices=DEVICE_NETWORK_STATUS_CHOICES,
        default=DEVICE_NETWORK_STATUS_DEACTIVATED)
    datetime_network_status_activated = models.DateTimeField(null=True)
    datetime_network_status_changed = models.DateTimeField(null=True)

    rx_partner = models.ForeignKey(
        'gdrives.PharmacyPartner', related_name='devices',
        null=True, on_delete=models.SET_NULL)
    date_shipped_to_rx_partner = models.DateField(null=True)
    # For devices that are marked as non conforming, they are either
    # segregated for rework or destruction.  Conforming devices
    # should have this as None.
    segregation_disposition = models.ForeignKey(
        'dropdowns.MeterDisposition', null=True, related_name='+', on_delete=models.SET_NULL)
    shipment = models.ForeignKey(
        'orders.OrderShipment', null=True, related_name='gdrives', on_delete=models.SET_NULL)
    reminder_text_sent = models.BooleanField(default=False)

    objects = GDriveManager()

    class Meta:
        verbose_name = "Device"

    @classmethod
    def generate_demo_meid(cls):
        return cls.generate_unique_value('meid')

    @classmethod
    def generate_demo_serial(cls):
        return cls.generate_unique_value('device_id')

    @classmethod
    def generate_demo_device(cls, **kwargs):
        return GDrive.objects.create_device(
            demo=True,
            meid=cls.generate_demo_meid(),
            device_id=cls.generate_demo_serial(),
            status=cls.DEVICE_STATUS_DEMO,
            **kwargs
        )

    @classmethod
    def generate_unique_value(cls, value_type):
        value_start = ('DEMOGDRIVE' if value_type == 'meid' else 'A') + '%04d'
        i = 1
        while i < pow(10, 4):
            new_val = value_start % i
            try:
                cls.objects.get(**{value_type: new_val})
            except cls.DoesNotExist:
                return new_val
            i += 1

    def __init__(self, *args, **kwargs):
        super(GDrive, self).__init__(*args, **kwargs)
        self._last_reading_checked = False

    def __str__(self) -> str:
        return ("Glucose Device %s" % (self.meid))

    def clear_patient(self, commit=True):
        self.patient = None
        self.last_assigned_patient = None
        self.unassigned_patients.clear()
        if commit:
            self.save()

    def display_assigned_date(self):
        if self.assigned_at:
            return self.assigned_at.strftime('%m/%d/%Y %I:%M %p')
        return 'N/A'

    def get_available_patients(self, group_only=False):
        """Gets all patients that can be assigned this device."""
        if not self.never_been_assigned():
            return User.objects.filter(pk=self.last_assigned_patient.pk)
        from genesishealth.apps.accounts.models import PatientProfile
        if group_only and self.group:
            queryset = self.group.get_patients()
        else:
            queryset = PatientProfile.objects.get_users()
        return queryset.filter(gdrives__isnull=True)

    def get_inspect_record(self):
        records = self.inspection_records.order_by('-datetime_inspected')
        if records.count() > 0:
            return records[0]

    def get_last_reading(self):
        if self.last_reading is None and not self._last_reading_checked:
            self._last_reading_checked = True
            try:
                self.last_reading = self.readings.order_by(
                    '-reading_datetime_utc')[0]
            except IndexError:
                pass
            else:
                self.save()
        return self.last_reading

    def get_last_reading_date(self, utc=False):
        reading = self.get_last_reading()
        if reading is not None:
            if utc:
                return reading.reading_datetime_utc
            return reading.reading_datetime

    def get_last_reading_date_utc(self):
        return self.get_last_reading_date(True)

    def get_non_conform_record(self):
        records = self.non_conformities.order_by('-datetime_added')
        if records.count() > 0:
            return records[0]

    def get_non_conformity_str(self):
        problems = set([])
        for problem in self.non_conformities.all():
            for typ in problem.non_conformity_types.all():
                problems.add(typ.name)
        return ", ".join(problems)

    def get_patient(self):
        if self.patient:
            return self.patient
        if self.unassigned_patients.count() > 0:
            return self.unassigned_patients.all()[0]

    def get_rework_record(self):
        records = self.rework_records.order_by('-datetime_reworked')
        if records.count() > 0:
            return records[0]

    def get_tracking_number(self):
        """Place holder for future."""
        return ''

    def is_available_to_patient(self, patient):
        """Whether or not the device has ever been assigned, even if it's not
        currently assigned."""
        return self.last_assigned_patient is None

    def is_available_to_new_patient(self):
        return self.never_been_assigned

    def is_inspectable(self):
        return self.status in (
            self.DEVICE_STATUS_REWORKED,
            self.DEVICE_STATUS_NEW,
            self.DEVICE_STATUS_FAILED_DELIVERY)

    def mark_failed_delivery(self):
        self.update_status(self.DEVICE_STATUS_FAILED_DELIVERY)
        self.clear_patient(commit=False)
        self.save()

    def mark_repairable(self, tray_number, disposition):
        self.update_status(self.DEVICE_STATUS_REPAIRABLE)
        self.tray_number = tray_number
        self.segregation_disposition = disposition
        self.save()

    def never_been_assigned(self):
        """Returns whether or not the device has never had a patient."""
        return self.last_assigned_patient is None

    def recover_readings(self, starting_date=None):
        """Goes through logs and creates readings for any entries in the log
        that do not exist.  Useful if a device has been taking readings before
        being put into the system.  Returns the number of new readings
        recovered."""
        recovered_count = 0
        kwargs = {
            'meid__iexact': self.meid, 'processing_succeeded': False,
            'recovered': False
        }
        reading_kwargs = {
            'patient__isnull': True
        }
        if starting_date is not None:
            kwargs['datetime__gte'] = starting_date
            reading_kwargs['reading_datetime_utc__gte'] = starting_date
        for entry in GDriveTransmissionLogEntry.objects.filter(**kwargs):
            if entry.recover():
                recovered_count += 1
        if self.patient is not None:
            for reading in self.readings.filter(**reading_kwargs):
                reading.patient = self.patient
                reading.save()
                recovered_count += 1
        return recovered_count

    def register(self, patient: User) -> None:
        """Updates the device with a new patient."""
        if self.patient:
            raise Exception(
                'Attempting to register a device that already has a patient')
        assert self.is_available_to_patient(patient)
        existing_device = patient.patient_profile.get_device()
        if existing_device is not None:
            existing_device.unregister()
        self.patient = patient
        self.patient.patient_profile._device = None
        self.update_status(self.DEVICE_STATUS_ASSIGNED)
        self.save()
        # Patient is no longer an "unassigned" patient if he was one.
        if patient in self.unassigned_patients.all():
            self.unassigned_patients.remove(patient)

    def register_is_synced(self):
        """Sees if this device is up to date with Verizon regarding
        registration status."""
        return (self.last_register_attempt ==
                self.last_confirmed_register_attempt)

    def rework(self):
        assert self.status == self.DEVICE_STATUS_REPAIRABLE
        self.update_status(self.DEVICE_STATUS_REWORKED)
        self.save()

    def save(self, *args, **kwargs):
        # Override save method to have it send register updates.
        if not self.assigned_at and self.patient:
            self.assigned_at = utcnow()

        if not self.last_assigned_patient and self.patient:
            self.last_assigned_patient = self.patient

        if self.group is None and self.patient and\
                self.patient.patient_profile.get_group():
            self.group = self.patient.patient_profile.get_group()

        super(GDrive, self).save(*args, **kwargs)

    def send_http_reading(self, **kwargs):
        """Sends HTTP reading to configured READING_SERVER_LOCATIONS."""
        from genesishealth.apps.readings.models import GlucoseReading
        reading_server = kwargs.pop('reading_server', None)
        raw_reading, reading_data = \
            GlucoseReading.generate_raw_reading_for_device(
                self, **kwargs)
        response = GlucoseReading.send_raw_reading(
            raw_reading, reading_server=reading_server)
        return response == 'success', reading_data

    def set_rx_partner(self, rx_partner):
        self.rx_partner = rx_partner
        if self.rx_partner is None:
            self.date_shipped_to_rx_partner = None
        else:
            self.date_shipped_to_rx_partner = now().date()
        self.save()

    def touch_status(self):
        """Runs when device receives a reading.  Updates status to working if
        it isn't already."""
        pass

    def unregister(self):
        """Unregisters the device from current patient."""
        if not self.patient:
            raise Exception(
                'Attempting to unregister a device without a patient.')
        self.unassigned_patients.add(self.patient)
        self.patient.patient_profile._device = None
        self.patient = None
        self.update_status(self.DEVICE_STATUS_UNASSIGNED)
        self.save()

    def update_status(self, new_status):
        self.status = new_status
        self.datetime_status_changed = now()
        if new_status == self.DEVICE_STATUS_ASSIGNED:
            self.datetime_assigned = now()
        elif new_status == self.DEVICE_STATUS_FAILED_DELIVERY:
            self.datetime_failed_delivery = now()
        elif new_status == self.DEVICE_STATUS_UNASSIGNED:
            self.datetime_replaced = now()
        elif new_status == self.DEVICE_STATUS_AVAILABLE:
            self.datetime_inspected = now()
        elif new_status == self.DEVICE_STATUS_REWORKED:
            self.datetime_reworked = now()
        elif new_status == self.DEVICE_STATUS_REPAIRABLE:
            self.datetime_repairable = now()
        elif new_status == self.DEVICE_STATUS_RETURNED:
            self.datetime_returned = now()

    def validate(self, user):
        assert self.is_inspectable()
        self.update_status(self.DEVICE_STATUS_AVAILABLE)
        self.segregation_disposition = MeterDisposition.objects.filter(
            is_problem=False)[0]
        self.save()
        GDriveInspectionRecord.objects.create(
            device=self, inspected_by=user)

    def was_ever_repairable(self):
        return self.non_conformities.count() > 0

    @property
    def ordinal(self):
        patient = self.patient or self.last_assigned_patient
        if not patient:
            return 'N/A'
        devices = patient.previous_devices.all() | patient.gdrives.all()
        devices = devices.order_by('created_at')
        gdrive_ids = [p.pk for p in devices]
        try:
            index = gdrive_ids.index(self.pk)
        except ValueError:
            pass
        else:
            return index + 1
        return 'N/A'


class GDriveTransmissionLogEntryManager(models.Manager):
    def get_entries_that_should_be_resolved(self):
        cutoff = now() - datetime.timedelta(
            seconds=settings.RESOLUTION_ALLOWANCE_TIME)
        return self.filter(
            datetime__lt=cutoff,
            datetime__gte=settings.AUDIT_START_DATE)


class GDriveTransmissionLogEntry(models.Model):
    """A record of a raw TCP transmission coming in over the network."""
    RESOLUTION_UNKNOWN_DEVICE = 'unknown_device'
    RESOLUTION_NO_PATIENT = 'no_patient'
    RESOLUTION_VALID = 'valid'
    RESOLUTION_INVALID = 'invalid'
    RESOLUTION_DUPLICATE = 'duplicate'
    RESOLUTION_PROCESSING_FAILED = 'processing_failed'
    RESOLUTION_INVALID_MEASURE = 'invalid_measure'
    RESOLUTION_UNRESOLVED = 'unresolved'

    RESOLUTION_OPTIONS = (
        (RESOLUTION_UNKNOWN_DEVICE, 'Unknown Device'),
        (RESOLUTION_NO_PATIENT, 'No Patient Assigned to Device'),
        (RESOLUTION_VALID, 'Successfully Processed'),
        (RESOLUTION_INVALID, 'Invalid Reading'),
        (RESOLUTION_DUPLICATE, 'Duplicate Reading'),
        (RESOLUTION_PROCESSING_FAILED, 'Processing Failed'),
        (RESOLUTION_INVALID_MEASURE, 'Invalid Measurement Type'),
        (RESOLUTION_UNRESOLVED, 'Unresolved')
    )

    datetime = models.DateTimeField(auto_now_add=True, db_index=True)
    content = models.TextField()
    decrypted_content = models.TextField(default="")
    error = models.TextField(default="")
    processing_succeeded = models.BooleanField()
    success_sent_to_client = models.BooleanField()
    reading_server = models.CharField(max_length=255, null=True)
    recovered = models.BooleanField(default=False)
    recovered_by = models.ForeignKey('auth.User', models.SET_NULL, null=True)
    recovered_time = models.DateTimeField(null=True)
    meid = models.CharField(max_length=255, null=True)
    glucose_value = models.IntegerField(null=True)
    resolution = models.CharField(
        max_length=255, choices=RESOLUTION_OPTIONS,
        default=RESOLUTION_UNRESOLVED, null=True)
    associated_patient_profile = models.ForeignKey(
        'accounts.PatientProfile', models.SET_NULL, null=True)
    reading = models.OneToOneField(
        'readings.GlucoseReading', models.SET_NULL, null=True,
        related_name="log_entry")
    sent_to_api = models.BooleanField(default=False)
    received_by_api = models.BooleanField(default=False)
    hide_from_qa_log = models.BooleanField(default=False)
    hide_from_orphaned_log = models.BooleanField(default=False)

    objects = GDriveTransmissionLogEntryManager()

    def _get_value(self, field_name):
        if not hasattr(self, '__data'):
            self.__data = json.loads(self.decrypted_content.replace("'", '"'))
        return self.__data[field_name]

    def determine_info(self):
        do_save = False
        if self.meid is None:
            if self.determine_meid(save=False):
                do_save = True
        if self.processing_succeeded:
            if self.reading is None:
                if self.determine_reading(save=False):
                    do_save = True
            if self.associated_patient_profile is None:
                if self.reading and self.reading.patient:
                    self.associated_patient_profile = self.reading\
                        .patient.patient_profile
                    do_save = True
        if do_save:
            self.save()
            return True

    def determine_meid(self, save=True):
        """Determines meid from decrypted_content."""
        if self.meid is not None:
            return
        try:
            self.meid = self._get_value('meid')
        except:
            return False
        if save:
            self.save()
        return True

    def determine_reading(self, save=True):
        """Determines reading from the data."""
        device = self.get_device()
        if device is None:
            return False
        # Look for readings on this device with our
        # glucose value with the same year, month, day,
        # and hour.
        glucose_value = int(self._get_value('value1'))
        year = int(self._get_value('year'))
        month = int(self._get_value('month'))
        day = int(self._get_value('day'))
        split_hour = self._get_value('hour').split(",")
        # Hour comes in strange format, so need to do some manipulation.
        hour = int(split_hour[0])
        start = pytz.UTC.localize(datetime.datetime(year, month, day, hour))
        # Apply offset.
        start += datetime.timedelta(hours=(-1 * int(split_hour[1])))
        end = start + datetime.timedelta(hours=1)
        candidates = device.readings.filter(
            reading_datetime_utc__range=(start, end),
            glucose_value=glucose_value)
        if candidates.count() == 1:
            self.reading = candidates[0]
            self.save()
            return True
        elif candidates.count() == 0:
            print("Could not find any reading matches for {0}".format(self.pk))
        elif candidates.count() > 1:
            print("Found multiple reading matches for {}".format(self.pk))
        return False

    def get_device(self):
        """Gets device associated with this log entry."""
        if self.meid is None:
            return
        try:
            return GDrive.objects.get(meid=self.meid)
        except GDrive.DoesNotExist:
            pass

    def get_glucose_value(self):
        return int(self._get_value('value1'))

    def get_meid(self):
        return self._get_value('meid')

    def get_measure_type(self):
        from genesishealth.apps.readings.models import GlucoseReading
        cleaned_measure_type = int(self._get_value('measure_type'))
        return GlucoseReading.parse_measure_type(cleaned_measure_type)

    def get_patient(self):
        if self.reading is not None:
            return self.reading.patient

    def recover(self):
        """Retries the data in the transmission log to create a reading."""
        from genesishealth.apps.readings.models import GlucoseReading
        success, decrypted_data, error_message, reading, patient = \
            GlucoseReading.process_reading(
                self.content, log_results=False)
        if success:
            self.reading = reading
            self.recovered = True
            self.save()
        return success

    def retro_resolve(self):
        """Determines resolution status retroactively."""
        if self.resolution not in (None, self.RESOLUTION_UNRESOLVED):
            return
        if not self.decrypted_content:
            self.resolution = self.RESOLUTION_INVALID
        elif self.processing_succeeded:
            self.resolution = self.RESOLUTION_VALID
        elif self.error:
            error_messages = {
                'Duplicate reading.': self.RESOLUTION_DUPLICATE,
                'Invalid device.': self.RESOLUTION_UNKNOWN_DEVICE,
                'Invalid measure type.': self.RESOLUTION_INVALID_MEASURE,
                'Device not associated with patient.':
                    self.RESOLUTION_NO_PATIENT
            }
            expected_error = self.error.replace(
                "Reading processing failed with error: ", "")
            self.resolution = error_messages.get(
                expected_error, self.RESOLUTION_PROCESSING_FAILED)
        else:
            self.resolution = self.RESOLUTION_UNRESOLVED
        self.save()


class GDriveLogEntry(models.Model):
    """Records a processed reading."""
    meid = models.CharField(max_length=255, null=True)
    device = models.ForeignKey(GDrive, null=True, on_delete=models.SET_NULL)
    date_created = models.DateTimeField(auto_now_add=True, db_index=True)
    reading_datetime_utc = models.DateTimeField(null=True, db_index=True)
    glucose_value = models.CharField(max_length=255, null=True)
    raw_data = models.TextField()
    successful = models.BooleanField()
    status = models.CharField(max_length=255, null=True)
    reading = models.OneToOneField(
        'readings.GlucoseReading', models.SET_NULL, null=True,
        related_name='gdrive_log_entry')
    hide_from_control_log = models.BooleanField(default=False)
    reading_server = models.ForeignKey(
        'monitoring.ReadingServer', null=True, related_name='log_entries', on_delete=models.SET_NULL)

    def device_exists(self):
        return self.device and 'Yes' or 'No'

    def reading_datetime(self):
        tz = pytz.timezone(settings.TIME_ZONE)
        return self.reading_datetime_utc.astimezone(tz)


class GDriveFirmwareVersion(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self) -> str:
        return self.name


class GDriveModuleVersion(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self) -> str:
        return self.name


class GDriveComplaint(models.Model):
    reported_problems = models.ManyToManyField(
        DeviceProblem, related_name='complaints')
    found_problems = models.ManyToManyField(
        DeviceProblem, related_name='+')
    device = models.ForeignKey(
        'GDrive', related_name='complaints', on_delete=models.CASCADE)
    description = models.TextField()
    datetime_added = models.DateTimeField(auto_now_add=True)
    datetime_modified = models.DateTimeField(auto_now=True)
    rma_return_date = models.DateField(null=True)
    added_by = models.ForeignKey(
        'auth.User', related_name='complaints_added', null=True, on_delete=models.SET_NULL)
    last_modified_by = models.ForeignKey(
        'auth.User', related_name='+', null=True, on_delete=models.SET_NULL)
    is_validated = models.BooleanField(default=False)
    is_resolved = models.BooleanField(default=False)
    validated_by = models.ForeignKey(
        'auth.User', related_name='+', null=True, on_delete=models.SET_NULL)
    rma_notes = models.TextField(null=True)

    def get_problem_str(self):
        problem_list = map(
            lambda x: x['name'],
            self.reported_problems.values('name'))
        return ", ".join(problem_list)

    def get_found_problem_str(self):
        problem_list = map(
            lambda x: x['name'],
            self.found_problems.values('name'))
        return ", ".join(problem_list)

    def touch(self, user):
        self.last_modified_by = user


class GDriveComplaintUpdate(models.Model):
    complaint = models.ForeignKey(GDriveComplaint, related_name='updates', on_delete=models.CASCADE)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='gdrive_complaint_updates',
        null=True, on_delete=models.SET_NULL)
    datetime_added = models.DateTimeField(auto_now_add=True)
    found_problems = models.ManyToManyField(
        DeviceProblem, related_name='+')
    rma_return_date = models.DateField(null=True)
    is_validated = models.BooleanField(default=False)
    rma_notes = models.TextField(null=True)

    def get_found_problem_str(self):
        problem_list = map(
            lambda x: x['name'],
            self.found_problems.values('name'))
        return ", ".join(problem_list)


class GDriveNonConformity(models.Model):
    non_conformity_types = models.ManyToManyField(
        'dropdowns.DeviceProblem',
        related_name='+')
    added_by = models.ForeignKey(
        'auth.User', null=True, related_name='+', on_delete=models.SET_NULL)
    device = models.ForeignKey(
        GDrive, related_name='non_conformities', on_delete=models.CASCADE)
    datetime_added = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
    tray_number = models.CharField(max_length=255)

    def get_problem_str(self):
        problem_list = map(
            lambda x: x['name'],
            self.non_conformity_types.values('name'))
        return ", ".join(problem_list)


class GDriveInspectionRecord(models.Model):
    device = models.ForeignKey(
        'GDrive', null=True, related_name='inspection_records', on_delete=models.SET_NULL)
    inspected_by = models.ForeignKey(
        'auth.User', null=True, related_name='inspection_records', on_delete=models.SET_NULL)
    datetime_inspected = models.DateTimeField(auto_now_add=True)


class GDriveReworkRecord(models.Model):
    device = models.ForeignKey(
        'GDrive', null=True, related_name='rework_records', on_delete=models.SET_NULL)
    reworked_by = models.ForeignKey(
        'auth.User', null=True, related_name='rework_records', on_delete=models.SET_NULL)
    datetime_reworked = models.DateTimeField(auto_now_add=True)
    details = models.TextField(verbose_name='Rework details')
    new_disposition = models.ForeignKey(
        'dropdowns.MeterDisposition', null=True, on_delete=models.SET_NULL)
    ready_for_inspection = models.BooleanField(default=False)


class PharmacyPartner(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self) -> str:
        return self.name


class GDriveManufacturerCarton(models.Model):
    number = models.CharField(max_length=255, unique=True)
    datetime_added = models.DateTimeField(auto_now_add=True)
    lot_number = models.CharField(max_length=255)
    date_shipped = models.DateField()
    is_inspected = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        'auth.User',
        related_name='manufacturer_cartons_approved',
        null=True, on_delete=models.SET_NULL)
    approved_datetime = models.DateTimeField(null=True)
    firmware_version = models.ForeignKey(
        'GDriveFirmwareVersion', null=True,
        related_name='devices', on_delete=models.SET_NULL)
    module_version = models.ForeignKey(
        'GDriveModuleVersion', null=True,
        related_name='devices', on_delete=models.SET_NULL)

    def __str__(self) -> str:
        return self.number

    def approve(self, approver):
        self.is_inspected = True
        self.approved_by = approver
        self.approved_datetime = now()
        self.save()
        for device in self.devices.filter(
                status=GDrive.DEVICE_STATUS_NEW):
            device.validate(approver)


class GDriveWarehouseCarton(models.Model):
    number = models.CharField(max_length=255, unique=True)
    datetime_added = models.DateTimeField(auto_now_add=True)
    is_shipped = models.BooleanField(default=False)
    shipment = models.ForeignKey(
        "orders.OrderShipment", null=True, related_name='warehouse_cartons', on_delete=models.SET_NULL)
    rx_partner = models.ForeignKey(
        'pharmacy.PharmacyPartner',
        null=True,
        related_name='warehouse_cartons', on_delete=models.SET_NULL)

    def __str__(self) -> str:
        return self.number

    def assign_to_shipment(self, shipment):
        self.is_shipped = True
        self.shipment = shipment
        self.save()

    def get_device_count(self):
        return self.devices.count()


class BloodPressureDevice(models.Model):
    patient = models.ForeignKey(
        User, limit_choices_to={'patient_profile__isnull': False},
        null=True, related_name='blood_pressure_devices', on_delete=models.SET_NULL)
    group = models.ForeignKey(
        'accounts.GenesisGroup', blank=True, null=True,
        related_name='blood_pressure_devices', on_delete=models.SET_NULL)
    meid = models.CharField(max_length=40)
    device_id = models.CharField(max_length=40)

    def __str__(self) -> str:
        return "Blood Pressure Device #%s" % self.meid


class WeightDevice(models.Model):
    patient = models.ForeignKey(
        User, limit_choices_to={'patient_profile__isnull': False},
        null=True, related_name='weight_devices', on_delete=models.SET_NULL)
    group = models.ForeignKey(
        'accounts.GenesisGroup', blank=True,
        null=True, related_name='weight_devices', on_delete=models.SET_NULL)
    meid = models.CharField(max_length=40)
    device_id = models.CharField(max_length=40)

    def __str__(self) -> str:
        return "Weight Device #%s" % self.meid
