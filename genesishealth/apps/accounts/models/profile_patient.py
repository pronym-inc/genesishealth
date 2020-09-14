import csv
import io
import math
import random
import re

from datetime import date, timedelta, datetime
from hashlib import sha1 as sha_constructor
from typing import Optional, Any

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Avg, Count
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.timezone import now, localtime

from genesishealth.apps.accounts.models.group import Company
from genesishealth.apps.accounts.models.profile_base import BaseProfile, ProfileManager
from genesishealth.apps.accounts.password import make_password
from genesishealth.apps.accounts.tasks import do_detect_timezone
from genesishealth.apps.api.models import APIPartner
from genesishealth.apps.dropdowns.models import DeactivationReason
from genesishealth.apps.health_information.models import (
    HealthInformation, HealthProfessionalTargets)
from genesishealth.apps.orders.models import Order, OrderCategory, OrderEntry
from genesishealth.apps.products.models import ProductType
from genesishealth.apps.readings.models import GlucoseReading
from genesishealth.apps.utils.tz_lookup import timezone_from_location_string


SHA1_RE = re.compile('^[a-f0-9]{40}$')
VALIDATION_STATUSES = (('active', 'active'), ('pending', 'pending'))


class PatientProfileManager(ProfileManager):
    def create_user(
            self,
            username: str,
            email: str,
            password: Optional[str] = None,
            email_password: bool = True,
            **kwargs: Any
    ) -> User:
        """Creates a patient.  This should rarely be used directly;
        instead use either the MyGHR or Verizon manager for this."""
        kwargs.setdefault('account_activation_datetime', now())
        patient = super(PatientProfileManager, self).create_user(
            username, email, password, email_password, **kwargs)
        patient.patient_profile.update_stat_averages()
        HealthInformation.objects.create(patient=patient)
        return patient

    def update_stat_averages(self) -> None:
        """Updates all of the last_week_average_* stats."""
        map(lambda x: x.update_stat_averages(), self.all())


class MyGHRPatientManager(PatientProfileManager):
    def create_user(
            self,
            first_name: str,
            last_name: str,
            password: Optional[str] = None,
            email=None, email_password=True, **kwargs):
        # Username will default to email, but if not provided, it will
        # generate one.
        passed_username = kwargs.pop('username', None)
        if passed_username:
            username = passed_username
        else:
            username = PatientProfile.generate_username(
                email=email, first_name=first_name, last_name=last_name)
        # Users without emails get a standard password.
        if password is None and not email:
            password = make_password()
        # Inherit some defaults from parent.
        company = kwargs.get('company')
        if company:
            if company.bin_id:
                kwargs['bin_number'] = company.bin_id
            if company.pcn_id:
                kwargs['pcn_number'] = company.pcn_id
            inherit_fields = (
                'glucose_strip_refill_frequency',
                'glucose_control_refill_frequency',
                'lancing_refill_frequency',
                'refill_method',
                'billing_method',
                'nursing_group'
            )
            for field in inherit_fields:
                val = getattr(company, field)
                if val is not None:
                    kwargs[field] = val
        patient = super(MyGHRPatientManager, self).create_user(
            username, email or '', password, email_password=email_password,
            first_name=first_name, last_name=last_name, **kwargs)
        if company and company.api_partner:
            patient.patient_profile.partners.add(company.api_partner)
        return patient

    def get_query_set(self):
        return super(MyGHRPatientManager, self).get_queryset().filter(
            is_myghr_user=True, is_scalability_user=False,
            is_verizon_patient=False)


class PatientProfile(BaseProfile):
    class GenesisReadingError(Exception):
        pass

    BILLING_METHOD_MEDICAL = 'medical'
    BILLING_METHOD_PHARMACY = 'pharmacy'
    BILLING_METHOD_CHOICES = (
        (BILLING_METHOD_MEDICAL, 'Medical'),
        (BILLING_METHOD_PHARMACY, 'Pharmacy')
    )

    ACTIVATED = "ALREADY_ACTIVATED"
    PREFERRED_CONTACT_EMAIL = 'email'
    PREFERRED_CONTACT_PHONE = 'phone'
    PREFERRED_CONTACT_METHOD_CHOICES = (
        (PREFERRED_CONTACT_EMAIL, 'Email'),
        (PREFERRED_CONTACT_PHONE, 'Phone')
    )

    GENDER_MALE = 'male'
    GENDER_FEMALE = 'female'
    GENDER_CHOICES = ((GENDER_MALE, 'Male'), (GENDER_FEMALE, 'Female'))

    ACCOUNT_STATUS_ACTIVE = 'active'
    ACCOUNT_STATUS_TERMED = 'termed'
    ACCOUNT_STATUS_SUSPENDED = 'suspended'

    ACCOUNT_STATUS_CHOICES = (
        (ACCOUNT_STATUS_ACTIVE, 'Active'),
        (ACCOUNT_STATUS_TERMED, 'Termed'),
        (ACCOUNT_STATUS_SUSPENDED, 'Suspended')
    )

    CSV_COLUMNS = (
        "Patient ID",
        "Insurance Identifier",
        "Username",
        "First Name",
        "Middle Initial",
        "Last Name",
        "Email",
        "Timezone",
        "Date of Birth",
        "Gender",
        "Address",
        "City",
        "State",
        "ZIP",
        "Phone",
        "Cell Phone",
        "Preferred Contact Method",
        "MEID",
        "Alerts"
    )

    REFILL_METHOD_SUBSCRIPTION = 'subscription'
    REFILL_METHOD_UTILIZATION = 'utilization'
    REFILL_METHOD_EMPLOYEE_FAMILY = 'employee_family'
    REFILL_METHOD_DEMO = 'demo'

    REFILL_METHOD_CHOICES = (
        (REFILL_METHOD_SUBSCRIPTION, 'Subscription'),
        (REFILL_METHOD_UTILIZATION, 'Utilization'),
        (REFILL_METHOD_EMPLOYEE_FAMILY, 'GHT Employee Family'),
        (REFILL_METHOD_DEMO, 'None / Demo')
    )

    user = models.OneToOneField(
        User, null=True, related_name='patient_profile', on_delete=models.SET_NULL)
    activation_key = models.CharField(
        blank=True, max_length=40, null=True, editable=False)
    preferred_contact_method = models.CharField(
        max_length=255,
        choices=PREFERRED_CONTACT_METHOD_CHOICES,
        default=PREFERRED_CONTACT_PHONE)
    api_username = models.CharField(
        blank=True, max_length=255, null=True, unique=True)
    created_by_group = models.ForeignKey(
        'GenesisGroup', related_name='created_patients', null=True, on_delete=models.SET_NULL)
    group = models.ForeignKey(
        'GenesisGroup', related_name='patients', null=True, on_delete=models.SET_NULL)
    insurance_identifier = models.CharField(
        blank=True, max_length=255, null=True, editable=False)
    last_reading = models.ForeignKey(
        'readings.GlucoseReading', related_name='+', null=True, editable=False, on_delete=models.SET_NULL)

    company = models.ForeignKey(
        Company, blank=True, null=True, related_name='patients', on_delete=models.SET_NULL)
    partners = models.ManyToManyField(APIPartner, blank=True,
                                      related_name='patients')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    date_of_birth = models.DateField(null=True)
    demo_patient = models.BooleanField(default=False)
    verizon_instance_id = models.CharField(max_length=255, null=True)
    verizon_demo = models.BooleanField(default=False)

    validation_status = models.CharField(
        choices=VALIDATION_STATUSES, max_length=100, editable=False, null=True)

    is_scalability_user = models.BooleanField(default=False)
    is_verizon_patient = models.BooleanField(default=False)
    is_myghr_user = models.BooleanField(default=True)
    account_status = models.CharField(
        max_length=255, choices=ACCOUNT_STATUS_CHOICES,
        default=ACCOUNT_STATUS_ACTIVE, editable=False)
    account_termination_date = models.DateTimeField(null=True)
    account_activation_datetime = models.DateTimeField(null=True)

    bin_number = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="BIN")
    pcn_number = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="PCN")
    billing_method = models.CharField(
        max_length=255, choices=BILLING_METHOD_CHOICES, null=True, blank=True)

    refill_method = models.CharField(
        max_length=255, choices=REFILL_METHOD_CHOICES, null=True, blank=True)

    glucose_strip_refill_frequency = models.PositiveIntegerField(
        null=True, blank=True)
    glucose_control_refill_frequency = models.PositiveIntegerField(
        null=True, blank=True)
    lancing_refill_frequency = models.PositiveIntegerField(
        null=True, blank=True)
    rx_partner = models.ForeignKey(
        'pharmacy.PharmacyPartner', null=True, related_name='patients', on_delete=models.SET_NULL)
    epc_member_identifier = models.CharField(max_length=255, null=True, blank=True)
    nursing_group = models.ForeignKey(
        'nursing.NursingGroup', null=True, related_name='patients', on_delete=models.SET_NULL)

    welcome_text_sent = models.BooleanField(default=False)

    objects = PatientProfileManager()
    myghr_patients = MyGHRPatientManager()

    class Meta:
        app_label = 'accounts'

    def __str__(self) -> str:
        return "%s profile" % (self.user and self.user.username or '')

    @classmethod
    def activate_user(cls, activation_key):
        if SHA1_RE.search(activation_key):
            try:
                profile = cls.objects.get(activation_key=activation_key)
            except cls.DoesNotExist:
                return False
            if not profile.activation_key_expired():
                user = profile.user
                user.is_active = True
                user.save()
                profile.activation_key = cls.ACTIVATED
                profile.save()
                return user
        return False

    @classmethod
    def generate_csv(cls, destination, patients):
        """Generate a CSV for the provided patients."""
        rows = [cls.CSV_COLUMNS, ]
        for patient in patients:
            rows.append(patient.patient_profile.generate_csv_row())
        with open(destination, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            for row in rows:
                writer.writerow(row)

    @classmethod
    def generate_csv2(cls, patients):
        """Returns string of content of CSV for provided patients."""
        rows = [cls.CSV_COLUMNS, ]
        for patient in patients:
            rows.append(patient.patient_profile.generate_csv_row())
        output = io.BytesIO()
        writer = csv.writer(output)
        for row in rows:
            writer.writerow(row)
        return output.getvalue()

    @classmethod
    def generate_username(
        cls, email=None, first_name=None, last_name=None, also_skip=None,
            skip_db_check=False):
        if also_skip is None:
            also_skip = []
        if email:
            return email
        if first_name and last_name:
            c = 0
            username_base = "{}.{}".format(first_name, last_name).replace(' ', '').lower()
            while True:
                new_username = username_base
                if c > 0:
                    new_username += "{}".format(c)
                c += 1
                if new_username in also_skip:
                    continue
                if skip_db_check:
                    return new_username
                try:
                    User.objects.get(username=new_username)
                except User.DoesNotExist:
                    return new_username
        else:
            # Look up other generically named users and figure out
            # next name.
            generic_prefix = 'ghtuser_'
            users = User.objects.filter(
                username__startswith=generic_prefix).order_by('-id')
            if len(users) == 0:
                start = 1
            else:
                start_str = users[0].username.replace(generic_prefix, '')
                start = int(start_str) + 1
            counter = start
            while True:
                candidate_name = "{0}{1}".format(generic_prefix, counter)
                try:
                    User.objects.get(username=candidate_name)
                except User.DoesNotExist:
                    break
                counter += 1
            return candidate_name

    def _get_business_partner(self):
        return self.get_group()

    def activation_key_expired(self):
        expiration_date = timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS)
        return self.activation_key == self.ACTIVATED or \
            (self.user.date_joined + expiration_date <= now())
    activation_key_expired.boolean = True

    def change_account_status(self, new_status, effective_date=None,
                              reason=None, notification_method="",
                              requested_by=None):
        valid_statuses = map(lambda x: x[0], self.ACCOUNT_STATUS_CHOICES)
        assert new_status in valid_statuses
        if new_status in (
                self.ACCOUNT_STATUS_TERMED,
                self.ACCOUNT_STATUS_SUSPENDED):
            self.account_termination_date = effective_date or now()
        self.account_status = new_status
        self.save()
        if effective_date is None:
            effective_date = localtime(now()).date()
        ActivationRecord.objects.create(
            patient=self.user,
            requested_by=requested_by,
            effective_date=effective_date,
            reason=reason,
            notification_method=notification_method,
            new_status=new_status
        )

    def check_for_refills(self):
        refill_method = self.get_refill_method()
        if refill_method == self.REFILL_METHOD_SUBSCRIPTION:
            do_refill = now() >= self.get_next_refill_date()
        elif refill_method == self.REFILL_METHOD_UTILIZATION:
            recent_readings = self.get_readings_since_last_refill()
            threshold = self.get_utilization_threshold()
            do_refill = recent_readings.count() >= threshold
        else:
            do_refill = False
        if do_refill:
            self.do_refill()

    def detect_timezone(self):
        if self.contact.zip:
            val = timezone_from_location_string(self.contact.zip)
            if val:
                strval = str(val)
                if strval != self.timezone_name:
                    self.timezone_name = strval
                    self.save()

    def detect_timezone_async(self):
        do_detect_timezone.delay(self.pk)

    def do_refill(self):
        refill_categories = OrderCategory.objects.filter(
            is_refill=True)
        if refill_categories.count() == 0:
            category = None
        else:
            category = refill_categories[0]
        # Add an entry for their strips.
        strip_quantity = self.get_strip_refill_amount_for_subscription_period()
        # Create an order.
        order = Order.objects.create(
            patient=self.user,
            order_origin=Order.ORDER_ORIGIN_AUTOMATIC_REFILL,
            category=category,
            order_status=Order.ORDER_STATUS_WAITING_TO_BE_SHIPPED,
            order_type=Order.ORDER_TYPE_PATIENT
        )
        if strip_quantity is None:
            return
        product_types = ProductType.objects.filter(
            category=ProductType.CATEGORY_STRIPS)
        if product_types.count() == 0:
            return
        product_type = product_types[0]
        OrderEntry.objects.create(
            order=order,
            quantity=strip_quantity,
            product=product_type)
        # Add on half as many boxes of lancets, rounded up
        lancet_quantity = int(math.ceil(float(strip_quantity) / 2))
        lancet_type = ProductType.objects.get(
            category=ProductType.CATEGORY_LANCET)
        OrderEntry.objects.create(
            order=order,
            quantity=lancet_quantity,
            product=lancet_type
        )

    def generate_activation_key(self):
        salt = sha_constructor(str(random.random())).hexdigest()[:5]
        email = self.user.email
        self.activation_key = sha_constructor(salt + email).hexdigest()

    def generate_csv_row(self):
        device = self.get_device()
        if device is None:
            meid = "N/A"
        else:
            meid = device.meid

        return [
            self.user.pk,
            self.insurance_identifier,
            self.user.username,
            self.user.first_name,
            self.contact.middle_initial,
            self.user.last_name,
            self.user.email,
            self.timezone_name,
            self.date_of_birth,
            self.gender,
            self.contact.address1,
            self.contact.city,
            self.contact.state,
            self.contact.zip,
            self.contact.phone,
            self.contact.cell_phone,
            self.preferred_contact_method,
            meid,
            ""
        ]

    def generate_standard_password(self):
        return make_password(self.user)

    def get_activation_record(self):
        try:
            return self.user.activation_records.order_by('-datetime_created')[0]
        except IndexError:
            pass

    def get_age(self):
        return int((date.today() - self.date_of_birth).days / 365.25)

    def get_alerts(self):
        return self.user.created_patientalerts.all()

    def get_anticipated_refill_date(self):
        last_order = self.get_last_refill_order()
        interval = timedelta(days=self.get_glucose_refill_shipping_interval())
        if last_order is None:
            return self.user.date_joined + interval
        if last_order.datetime_shipped is None:
            return last_order.datetime_added + interval
        return last_order.datetime_shipped + interval

    def get_average_daily_readings(self, days=7):
        if days == 0:
            return 0
        before = now() - timedelta(days=days)
        readings = self.user.glucose_readings.filter(
            reading_datetime_utc__range=(before, now()))
        return float(readings.count()) / days

    def get_average_glucose_level(self, days=7, measure_type=None):
        before = now() - timedelta(days=days)
        readings = self.user.glucose_readings.filter(
            reading_datetime_utc__range=(before, now()))

        if measure_type:
            readings = readings.filter(measure_type=measure_type)

        aggregates = readings.aggregate(Avg('glucose_value'))

        return aggregates['glucose_value__avg']

    def get_caregiver(self):
        if self.professionals.count() > 0:
            return self.professionals.all()[0]

    def get_compliance_goal_for_professional(self, professional):
        targets = self.get_health_targets_for_professional(professional)
        return targets.compliance_goal

    def get_days_tested_for_period(self, start_date, end_date):
        days_tested = set([])
        for reading in GlucoseReading.objects.filter(
                patient=self.user,
                reading_datetime_utc__gte=start_date,
                reading_datetime_utc__lt=end_date + timedelta(days=1)):
            days_tested.add(reading.reading_datetime_utc.date())
        return len(days_tested)

    def _get_device(self):
        try:
            return self.user.gdrives.all()[0]
        except IndexError:
            return

    def get_device(self):
        return self._get_device()

    def get_device_assigned_date(self, format='%m/%d/%Y %I:%M %p'):
        device = self.get_device()
        if device and device.assigned_at:
            date_str = device.assigned_at.strftime(format)
            if date_str:
                return date_str
        return 'N/A'

    def get_glucose_refill_interval(self) -> int:
        if self.get_refill_method() != self.REFILL_METHOD_SUBSCRIPTION:
            return settings.DEFAULT_SUBSCRIPTION_REFILL_INTERVAL_DAYS
        if self.glucose_strip_refill_frequency is not None:
            return self.glucose_strip_refill_frequency
        if (self.company is not None and
                self.company.glucose_strip_refill_frequency is not None):
            return self.company.glucose_strip_refill_frequency
        return settings.DEFAULT_SUBSCRIPTION_REFILL_INTERVAL_DAYS

    def get_glucose_refill_shipping_interval(self) -> int:
        return self.get_glucose_refill_interval() - settings.DEFAULT_SUBSCRIPTION_REFILL_SHIPPING_BUFFER_DAYS

    def get_group(self):
        return self.group

    def get_health_targets_for_professional(self, professional):
        return HealthProfessionalTargets.objects.get_or_create(
            patient=self.user, professional=professional)

    def get_last_reading(self):
        readings = self.user.glucose_readings.order_by('-reading_datetime_utc')
        if readings.count() > 0:
            return readings[0]

    def get_last_reading_date(self):
        last_reading = self.get_last_reading()
        if last_reading:
            return last_reading.reading_datetime.strftime(
                '%m/%d/%Y %I:%M %p')
        return 'N/A'

    def get_last_reading_display(self):
        last_reading = self.get_last_reading_date()
        if last_reading == 'N/A':
            return None
        return last_reading

    def get_last_refill_datetime(self) -> datetime:
        last_refill = self.get_last_shipped_refill_order()
        if last_refill:
            return last_refill.datetime_shipped
        return self.user.date_joined

    def get_last_refill_order(self) -> Optional[Order]:
        orders = self.user.orders.filter(category__is_refill=True).order_by('-datetime_added')
        if orders.count() == 0:
            return None
        return orders[0]

    def get_last_shipped_refill_order(self) -> Optional[Order]:
        orders = self.user.orders.filter(
            category__is_refill=True,
            datetime_shipped__isnull=False
        ).order_by('-datetime_shipped')
        if orders.count() == 0:
            return None
        return orders[0]

    def get_next_refill_date(self) -> Optional[datetime]:
        if self.get_refill_method() != self.REFILL_METHOD_SUBSCRIPTION:
            return
        last_refill = self.get_last_refill_order()
        refill_interval = self.get_glucose_refill_shipping_interval()
        if last_refill is None:
            base_date = self.user.date_joined
        else:
            if last_refill.datetime_shipped:
                base_date = last_refill.datetime_shipped
            else:
                base_date = last_refill.datetime_added
        return base_date + timedelta(days=refill_interval)

    def get_partner_string(self) -> str:
        return ", ".join(map(lambda x: x['name'],self.partners.all().values('name')))

    def get_professionals(self):
        return self.professionals.all()

    def get_readings_since_last_refill(self):
        last_refill = self.get_last_refill_order()
        readings = self.user.glucose_readings.all()
        if last_refill is not None:
            if last_refill.datetime_shipped:
                readings = readings.filter(
                    reading_datetime_utc__gte=last_refill.datetime_shipped)
            else:
                readings = readings.filter(
                    reading_datetime_utc__gte=last_refill.datetime_added)
        return readings

    def get_refill_method(self):
        if self.refill_method:
            return self.refill_method
        if self.company is not None:
            return self.company.refill_method

    def get_strip_refill_amount_for_subscription_period(self):
        # Figure out their average daily readings then figure
        # out how many strips to send them to last 90 days.
        days = (now() - self.get_last_refill_datetime()).days
        average_readings = self.get_average_daily_readings(days)
        reading_period = self.get_glucose_refill_interval()
        expected_readings_for_period = average_readings * reading_period + 10
        boxes_used = int(math.ceil(expected_readings_for_period / 50))
        boxes_used = max(boxes_used, self.get_strip_refill_minimum())
        return boxes_used

    def get_strip_refill_minimum(self):
        if (self.company is not None and
                self.company.minimum_refill_quantity is not None):
            return self.company.minimum_refill_quantity
        return 3

    def get_total_tests_for_period(self, start, end):
        return GlucoseReading.objects.filter(
            patient=self.user,
            reading_datetime_utc__gte=start,
            reading_datetime_utc__lt=end + timedelta(days=1)).count()

    def get_utilization_threshold(self):
        last_refill = self.get_last_refill_order()
        if last_refill is None:
            base_quantity = self.get_strip_refill_minimum()
        else:
            try:
                entry = last_refill.entries.get(
                    product__category=ProductType.CATEGORY_STRIPS)
            except OrderEntry.DoesNotExist:
                base_quantity = self.get_strip_refill_minimum()
            else:
                base_quantity = entry.quantity
        # Each box is 50 readings.
        return int(base_quantity * 50 * settings.DEFAULT_UTILIZATION_REFILL_THRESHOLD_PERCENTAGE)

    def group_list(self):
        return self.group.name if self.group else 'N/A'

    def login_type(self):
        return "Patient"

    def readable_gender(self):
        for k, v in PatientProfile.GENDER_CHOICES:
            if k == self.gender:
                return v

    def register_device(self, device, replace=True):
        """Registers a device to the user."""
        if not replace and self.get_device():
            raise Exception('Patient already has device assigned.')
        self.replace_device(device)

    def remove_caregiver(self):
        for professional in self.get_professionals():
            professional.patients.remove(self)

    def replace_device(self, device):
        """Replaces any existing device with the provided one."""
        for r_device in self.user.gdrives.exclude(pk=device.pk):
            self.unregister_device(r_device)
        if self.get_device() == device:
            return
        device.register(self.user)

    def save(self, *args, **kwargs):
        super(PatientProfile, self).save(*args, **kwargs)
        # Make sure contact always stays up to date.
        shared_fields = ('first_name', 'last_name', 'email')
        for sf in shared_fields:
            setattr(self.contact, sf, getattr(self.user, sf))
        self.contact.save()

    def send_activation_email(self):
        activation_link = 'http://{}/accounts/activate/{}/'.format(
            settings.SITE_URL, self.activation_key)
        ctx_dict = {'activation_key': self.activation_key,
                    'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
                    'activation_link': activation_link}
        subject = render_to_string('accounts/activation/email_subject.txt',
                                   ctx_dict)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())

        message = render_to_string('accounts/activation/email.txt',
                                   ctx_dict)

        self.user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)

    def send_http_reading(self, **kwargs):
        """Sends HTTP reading to configured READING_SERVER_LOCATIONS."""
        reading_server = kwargs.pop('reading_server', None)
        raw_reading, reading_data = GlucoseReading.generate_raw_reading(self.user, **kwargs)
        response = GlucoseReading.send_raw_reading(raw_reading, reading_server=reading_server)
        return response == b'success', reading_data

    def set_phone_number(self, number):
        self.contact.phone_numbers.all().delete()
        self.contact.add_phone(number)

    def target_range_breakdown(self, professional=None):
        if professional:
            targets = HealthProfessionalTargets.objects.get_or_create(
                professional=professional, patient=self.user)
        else:
            targets = self.user.healthinformation
        value_breakdown = [
            'AVG: {} - {}'.format(
                targets.premeal_glucose_goal_minimum,
                targets.postmeal_glucose_goal_maximum),
            'PRE: {} - {}'.format(
                targets.premeal_glucose_goal_minimum,
                targets.premeal_glucose_goal_maximum),
            'POST: {} - {}'.format(
                targets.postmeal_glucose_goal_minimum,
                targets.postmeal_glucose_goal_maximum)
        ]
        return ', '.join(value_breakdown)

    def unregister_device(self, device=None):
        if device is None:
            device = self.get_device()
        if not device:
            raise Exception(
                'Attempting to unregister a device from a user that does '
                'not have one.')
        device.unregister()

    def update_stat_averages(self):
        try:
            stat_record = self.stats
        except PatientStatisticRecord.DoesNotExist:
            stat_record = PatientStatisticRecord(profile=self)
        stat_record.update()


@receiver(post_save, sender=PatientProfile)
def post_save_patient_profile(
        sender, instance, created, raw, using, **kwargs):
    if created:
        instance.detect_timezone_async()
        # Inherit BIN and PCN from company if left blank.
        if instance.company is not None:
            changed = False
            if instance.company.bin_id and not instance.bin_number:
                instance.bin_number = instance.company.bin_id
                changed = True
            if instance.company.pcn_id and not instance.pcn_number:
                instance.pcn_number = instance.company.pcn_id
                changed = True
            if changed:
                instance.save()


class PatientStatisticRecord(models.Model):
    profile = models.OneToOneField(PatientProfile, related_name='stats', on_delete=models.CASCADE)

    readings_last_1 = models.FloatField(null=True)
    average_value_last_1 = models.FloatField(null=True)

    readings_last_7 = models.FloatField(null=True)
    average_value_last_7 = models.FloatField(null=True)

    readings_last_14 = models.FloatField(null=True)
    average_value_last_14 = models.FloatField(null=True)

    readings_last_30 = models.FloatField(null=True)
    average_value_last_30 = models.FloatField(null=True)

    readings_last_60 = models.FloatField(null=True)
    average_value_last_60 = models.FloatField(null=True)

    readings_last_90 = models.FloatField(null=True)
    average_value_last_90 = models.FloatField(null=True)

    readings_last_180 = models.FloatField(null=True)
    average_value_last_180 = models.FloatField(null=True)

    class Meta:
        app_label = 'accounts'

    def update(self):
        for i in (1, 7, 14, 30, 60, 90, 180):
            qs = self.profile.user.glucose_readings.filter(
                reading_datetime_utc__gte=(now() - timedelta(days=i)))
            aggs = qs.aggregate(
                Avg('glucose_value'), Count('glucose_value'))
            readings_field_name = "readings_last_{}".format(i)
            average_value_field_name = "average_value_last_{}".format(i)
            setattr(self, readings_field_name,
                    float(aggs['glucose_value__count']) / i)
            setattr(self, average_value_field_name, aggs['glucose_value__avg'])
        self.save()


class ActivationRecord(models.Model):
    REASON_BUSINESS_ASSOCIATE = 'business_associate'
    REASON_DECEASED = 'deceased'
    REASON_PENDING_UPDATE = 'pending_update'
    REASON_INACTIVE = 'inactive'
    REASON_INSURANCE_DENIED = 'insurance_denied'
    REASON_PACKAGE_RETURNED = 'package_returned'
    REASON_OPTED_OUT = 'opted_out'
    REASON_TERMED = 'termed'
    REASON_CHOICES = (
        (REASON_BUSINESS_ASSOCIATE, 'Business Associate'),
        (REASON_DECEASED, 'Deceased'),
        (REASON_PENDING_UPDATE, 'Hold Pending Info Update'),
        (REASON_INACTIVE, 'Inactive'),
        (REASON_INSURANCE_DENIED, 'Insurance Denied'),
        (REASON_PACKAGE_RETURNED, 'Package Returned'),
        (REASON_OPTED_OUT, 'Patient Opted Out'),
        (REASON_TERMED, 'Termed')
    )

    patient = models.ForeignKey(
        'auth.User', null=True, related_name='activation_records', on_delete=models.SET_NULL)
    effective_date = models.DateField()
    reason = models.ForeignKey(
        DeactivationReason, null=True, related_name='+', on_delete=models.SET_NULL)
    datetime_created = models.DateTimeField(auto_now_add=True)
    requested_by = models.ForeignKey(
        'auth.User', null=True, related_name='requested_activation_records', on_delete=models.SET_NULL)
    notification_method = models.TextField()
    new_status = models.CharField(
        max_length=255, choices=PatientProfile.ACCOUNT_STATUS_CHOICES)


class PatientCommunication(models.Model):
    SUBJECT_INBOUND_EPC = 'inbound_epc'
    SUBJECT_INBOUND_OTHER = 'inbound_other'
    SUBJECT_INBOUND_EMAIL = 'inbound_email'
    SUBJECT_OUTBOUND = 'outbound'

    SUBJECT_CHOICES = (
        (SUBJECT_INBOUND_EPC, 'Inbound call EPC'),
        (SUBJECT_INBOUND_OTHER, 'Inbound call other'),
        (SUBJECT_INBOUND_EMAIL, 'Inbound email'),
        (SUBJECT_OUTBOUND, 'Outbound call')
    )

    patient = models.ForeignKey(
        'auth.User', null=True, related_name='communications', on_delete=models.SET_NULL)
    subject = models.CharField(
        max_length=255, choices=SUBJECT_CHOICES)
    description = models.TextField()
    category = models.ForeignKey(
        'dropdowns.CommunicationCategory', related_name='communications',
        limit_choices_to={'is_active': True}, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(
        'dropdowns.CommunicationSubcategory', related_name='communications', on_delete=models.CASCADE)
    status = models.ForeignKey(
        'dropdowns.CommunicationStatus', related_name='+', null=True, on_delete=models.SET_NULL)
    added_by = models.ForeignKey(
        'auth.User', null=True, related_name='communications_added', on_delete=models.SET_NULL)
    resolution = models.ForeignKey(
        'dropdowns.CommunicationResolution', null=True, related_name='+', on_delete=models.SET_NULL)
    datetime_added = models.DateTimeField(default=now)
    datetime_updated = models.DateTimeField()
    datetime_closed = models.DateTimeField(null=True)
    last_updated_by = models.ForeignKey(
        'auth.User', null=True, related_name='+', on_delete=models.SET_NULL)

    def last_entry_datetime(self):
        notes = self.notes.order_by('-datetime_added')
        if notes.count() == 0:
            return self.datetime_added
        return notes[0].datetime_added

    def touch(self, user):
        self.last_updated_by = user
        self.datetime_updated = now()


class PatientCommunicationNote(models.Model):
    QI_CATEGORY_FEEDBACK = 'feedback'
    QI_CATEGORY_COMPLAINT = 'complaint'

    QI_CATEGORY_CHOICES = (
        (QI_CATEGORY_COMPLAINT, 'Complaint'),
        (QI_CATEGORY_FEEDBACK, 'Feedback')
    )

    communication = models.ForeignKey(
        'PatientCommunication', null=True, related_name='notes', on_delete=models.SET_NULL)
    quality_improvement_category = models.CharField(
        max_length=255, choices=QI_CATEGORY_CHOICES)
    has_replacements = models.BooleanField(
        default=False, verbose_name='Replace Genesis products')
    is_rma = models.BooleanField(
        default=False, verbose_name='Request Warranty Authorization (RA)')
    replacements = models.ManyToManyField(
        'products.ProductType', related_name='+')
    added_by = models.ForeignKey(
        'auth.User', null=True, related_name='communication_notes', on_delete=models.SET_NULL)
    datetime_added = models.DateTimeField(auto_now_add=True)
    content = models.TextField(verbose_name='Agent notes')
    change_status_to = models.ForeignKey(
        'dropdowns.CommunicationStatus', related_name='+', on_delete=models.CASCADE)
    resolution = models.ForeignKey(
        'dropdowns.CommunicationResolution', null=True,
        related_name='+', on_delete=models.SET_NULL)

    class Meta:
        ordering = ('-datetime_added',)

    def get_replacement_string(self):
        return ", ".join(map(
            lambda x: x['name'],
            self.replacements.values('name')
        ))
