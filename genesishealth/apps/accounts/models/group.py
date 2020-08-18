import csv
import io
from datetime import timedelta, datetime
from typing import List, Optional, TYPE_CHECKING

from django.db import models
from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.utils.timezone import make_naive, get_default_timezone

from genesishealth.apps.accounts.models import PatientProfile
from genesishealth.apps.accounts.reports import _generate_noncompliance_report, _generate_target_range_report
from genesishealth.apps.epc.models import EPCOrder
from genesishealth.apps.gdrives.models import GDrive


class GenesisGroup(models.Model):
    HEALTHCARE_PROVIDER = 'healthcare_provider'
    INSURANCE_ADMINISTRATOR = 'insurance_administrator'
    DISEASE_MANAGEMENT_ORGANIZATION = 'disease_management_organization'
    PHARMACIST = 'pharmacist'
    PII_RESTRICTED = 'pii_restricted'

    GROUP_TYPE_CHOICES = (
        (HEALTHCARE_PROVIDER, 'Healthcare Provider'),
        (INSURANCE_ADMINISTRATOR, 'Insurance Administrator'),
        (DISEASE_MANAGEMENT_ORGANIZATION, 'Disease Management Organization'),
        (PHARMACIST, 'Pharmacist'),
        (PII_RESTRICTED, 'PII Restricted')
    )

    name = models.CharField(max_length=255, unique=True)
    group_type = models.CharField(max_length=255, choices=GROUP_TYPE_CHOICES)
    contact = models.ForeignKey('Contact', on_delete=models.CASCADE)
    is_demo_group = models.BooleanField(default=False)
    skip_device_deactivation = models.BooleanField(default=False)
    is_no_pii = models.BooleanField(default=False)
    should_generate_refill_files = models.BooleanField(default=False)
    exclude_from_orders = models.BooleanField(default=False)

    class Meta:
        app_label = 'accounts'

    def __str__(self) -> str:
        return self.name

    def add_patient(self, patient: User) -> None:
        """This method updates an existing relationship if it already exists"""
        patient.patient_profile.group = self
        patient.patient_profile.save()

    def generate_inactive_participation_status_report(self, start: datetime, end: datetime) -> str:
        rows = []
        end_plus = end + timedelta(days=1)
        query = """
        SELECT
            u.id,
            MAX(u.first_name) AS first_name,
            MAX(u.last_name) AS last_name,
            MAX(u.date_joined) AS date_joined,
            MAX(p.account_status) AS account_status,
            MAX(p.account_activation_datetime) AS account_activation_datetime,
            MAX(p.account_termination_date) AS account_termination_date,
            MAX(p.epc_member_identifier) AS epc_member_identifier,
            COUNT(DISTINCT(r.id)) AS readings_taken,
            COUNT(DISTINCT to_char(r.reading_datetime_utc AT TIME ZONE 'America/Chicago', 'YYYY-MM-DD')) AS days_reading_taken,
            MAX(p.insurance_identifier) AS insurance_identifier,
            MAX(l.date_created) AS last_reading_datetime,
            MAX(r.reading_datetime_utc) AS last_reading_timestamp,
            MAX(c.name) AS company_name,
            MAX(pn.phone) AS phone_number,
            MAX(con.address1) AS address1,
            MAX(con.address2) AS address2,
            MAX(con.city) AS city,
            MAX(con.state) AS state,
            MAX(con.zip) AS zip,
            MAX(p.gender) AS gender,
            MAX(p.date_of_birth) AS date_of_birth,
            MAX(d.meid) AS meid
        FROM auth_user u
            LEFT JOIN accounts_patientprofile p
                ON u.id = p.user_id
            LEFT JOIN readings_glucosereading r
                ON u.id = r.patient_id
            LEFT JOIN gdrives_gdrive d
                ON d.patient_id = u.id
            LEFT JOIN gdrives_gdrivelogentry l
                ON l.reading_id = r.id
            LEFT JOIN accounts_company c
                ON p.company_id = c.id
            LEFT JOIN accounts_contact con
                ON p.contact_id = con.id
            LEFT JOIN accounts_phonenumber pn
                ON con.id = pn.contact_id
        WHERE
            p.id IS NOT NULL AND
            p.group_id = %s AND
            p.account_activation_datetime < %s AND
            r.reading_datetime_utc > p.account_activation_datetime
        GROUP BY u.id, u.date_joined
        """  # noqa
        total_days = int((end_plus - start).total_seconds() / 24 / 60 / 60)
        dt_format = '%Y-%m-%d 00:00:00 America/Chicago'
        end_date = end_plus.strftime(dt_format)
        patients = User.objects.raw(
            query,
            [self.id, end_date])
        patient_count = 0
        tz = get_default_timezone()
        for patient in patients:
            patient_count += 1
            total_tests = patient.readings_taken
            days_tested = patient.days_reading_taken if total_tests > 0 else 0
            dt_format = "%m/%d/%y %I:%M:%S %p"
            if patient.last_reading_datetime:
                dt = make_naive(patient.last_reading_datetime, tz)
                dt_string = dt.strftime(dt_format)
            else:
                dt_string = "N/A"
            if patient.last_reading_timestamp:
                dt = make_naive(patient.last_reading_timestamp, tz)
                reading_dt_string = dt.strftime(dt_format)
            else:
                reading_dt_string = "N/A"
            account_created_string = patient.date_joined.strftime("%m/%d/%Y")
            if patient.account_termination_date:
                account_terminated_string = \
                    patient.account_termination_date.strftime("%m/%d/%Y")
            else:
                account_terminated_string = "N/A"
            if (patient.account_status == "active" and
                    patient.account_activation_datetime):
                account_activation_string = \
                    patient.account_activation_datetime.strftime("%m/%d/%Y")
                enrolled_age_days = (
                    end - patient.account_activation_datetime.date()).days
            else:
                account_activation_string = "N/A"
                enrolled_age_days = 0
            orders = EPCOrder.objects.filter(
                epc_member__user__id=patient.id,
                order_date__range=(start, end),
                order_status__in=["SHIPPED", "SENT"]).order_by(
                'order_date')
            meter_shipped_count = strips_shipped_count = 0
            orders_shipped_count = orders.count()
            order_dates = []
            for order in orders:
                if order.meter_shipped:
                    meter_shipped_count += order.meter_shipped
                if order.strips_shipped:
                    strips_shipped_count += order.strips_shipped
                order_dates.append(order.order_date.strftime("%Y/%m/%d"))
            shipped_date_str = ", ".join(order_dates)
            new_row = [
                patient.company_name,
                patient.first_name,
                patient.last_name,
                patient.account_status,
                patient.insurance_identifier,
                patient.epc_member_identifier,
                patient.meid,
                patient.date_of_birth,
                patient.gender,
                account_created_string,
                account_activation_string,
                account_terminated_string,
                enrolled_age_days,
                total_days,
                days_tested,
                round(float(total_tests) / days_tested, 2) if days_tested > 0
                else 0,
                round(100 * float(days_tested) / total_days, 2)
                if total_days > 0 else 0,
                total_tests,
                dt_string,
                reading_dt_string,
                meter_shipped_count,
                strips_shipped_count,
                orders_shipped_count,
                shipped_date_str
            ]
            rows.append(new_row)

        output = io.StringIO()
        writer = csv.writer(output)
        # Write hreaders
        header_rows = [
            ['Title', 'Inactive Participation Status Report'],
            ['Date', '{} - {}'.format(start, end)],
            ['Group', self.name],
            ['Number of Patients', patient_count],
            [],
        ]
        header_rows.append([
            'Group',
            'First Name',
            'Last Name',
            'Account Status',
            'Insurance ID',
            'EPC ID',
            'MEID',
            'Date of Birth',
            'Gender',
            'AccountCreated',
            'Activation Date',
            'Inactive Date',
            'Enrolled Age',
            'Days',
            'Days Tested',
            'Avg Tests/Days Tested',
            '% Days Tested',
            'Total Tests',
            'Server Timestamp (CST)',
            'Reading Timestamp (CST)',
            'Meters',
            'Strips',
            'Orders',
            'Shipped Dates'
        ])
        for hr in header_rows:
            writer.writerow(hr)
        for row in rows:
            writer.writerow(row)
        content = output.getvalue()
        return content

    def generate_noncompliance_report(self, hours: int) -> str:
        return _generate_noncompliance_report(
            self.get_patients(),
            hours,
            self.name,
            no_pii=self.is_no_pii
        )

    def generate_participation_report(self, start: datetime, end: datetime) -> str:
        rows = []
        end_plus = end + timedelta(days=1)
        query = """
        SELECT
            u.id,
            u.first_name,
            u.last_name,
            COUNT(r.id) AS readings_taken,
            COUNT(DISTINCT to_char(r.reading_datetime_utc AT TIME ZONE 'America/Chicago', 'YYYY-MM-DD')) AS days_reading_taken,
            d.meid AS meid,
            p.insurance_identifier AS insurance_identifier,
            p.epc_member_identifier AS epc_member_identifier,
            MAX(l.date_created) AS last_reading_datetime,
            MAX(r.reading_datetime_utc) AS last_reading_timestamp,
            c.name AS company_name
        FROM auth_user u
            LEFT JOIN accounts_patientprofile p
                ON u.id = p.user_id
            LEFT JOIN readings_glucosereading r
                ON u.id = r.patient_id AND r.reading_datetime_utc BETWEEN %s AND %s
            LEFT JOIN gdrives_gdrive d
                ON d.patient_id = u.id
            LEFT JOIN gdrives_gdrivelogentry l
                ON l.reading_id = r.id
            LEFT JOIN accounts_company c
                ON p.company_id = c.id
        WHERE p.id IS NOT NULL AND p.group_id = %s
        GROUP BY u.id, u.first_name, u.last_name, d.meid, p.insurance_identifier, c.name, p.epc_member_identifier
        """  # noqa
        total_days = int((end_plus - start).total_seconds() / 24 / 60 / 60)
        dt_format = '%Y-%m-%d 00:00:00 America/Chicago'
        start_date = start.strftime(dt_format)
        end_date = end_plus.strftime(dt_format)
        patients = User.objects.raw(query, [start_date, end_date, self.id])
        patient_count = 0
        tz = get_default_timezone()
        for patient in patients:
            patient_count += 1
            total_tests = patient.readings_taken
            days_tested = patient.days_reading_taken if total_tests > 0 else 0
            dt_format = "%m/%d/%y %I:%M:%S %p"
            if patient.last_reading_datetime:
                dt = make_naive(patient.last_reading_datetime, tz)
                dt_string = dt.strftime(dt_format)
            else:
                dt_string = "N/A"
            if patient.last_reading_timestamp:
                dt = make_naive(patient.last_reading_timestamp, tz)
                reading_dt_string = dt.strftime(dt_format)
            else:
                reading_dt_string = "N/A"
            if self.is_no_pii:
                new_row = [
                    patient.company_name,
                    patient.epc_member_identifier,
                    patient.id
                ]
            else:
                new_row = [
                    patient.company_name,
                    patient.first_name,
                    patient.last_name,
                    patient.insurance_identifier
                ]
            new_row.extend([
                patient.meid if patient.meid else 'N/A',
                total_days,
                days_tested,
                round(float(total_tests) / days_tested, 2)
                if days_tested > 0 else 0,
                round(100 * float(days_tested) / total_days, 2)
                if total_days > 0 else 0,
                total_tests,
                dt_string,
                reading_dt_string
            ])
            rows.append(new_row)

        output = io.StringIO()
        writer = csv.writer(output)
        # Write hreaders
        header_rows: List[List[str]] = [
            ['Title', 'Group Participation Report'],
            ['Date', '{} - {}'.format(start, end)],
            ['Group', str(self.name)],
            ['Number of Patients', str(patient_count)],
            [],
        ]
        if self.is_no_pii:
            header_rows.append([
                'Group',
                'EPC ID',
                'GHT ID',
                'Active MEID',
                'Days',
                'Days Tested',
                'Avg Tests/Days Tested',
                '% Days Tested',
                'Total Tests',
                'Server Timestamp (CST)',
                'Reading Timestamp (CST)'
            ])
        else:
            header_rows.append([
                'Group',
                'First Name',
                'Last Name',
                'Insurance ID',
                'Active MEID',
                'Days',
                'Days Tested',
                'Avg Tests/Days Tested',
                '% Days Tested',
                'Total Tests',
                'Server Timestamp (CST)',
                'Reading Timestamp (CST)'
            ])
        for hr in header_rows:
            writer.writerow(hr)
        for row in rows:
            writer.writerow(row)
        content = output.getvalue()
        return content

    def generate_participation_status_report(self, start, end):
        rows = []
        end_plus = end + timedelta(days=1)
        query = """
        SELECT
            u.id,
            MAX(u.first_name) AS first_name,
            MAX(u.last_name) AS last_name,
            MAX(u.date_joined) AS date_joined,
            MAX(p.account_status) AS account_status,
            MAX(p.account_termination_date) AS account_termination_date,
            MAX(p.epc_member_identifier) AS epc_member_identifier,
            COUNT(DISTINCT(r.id)) AS readings_taken,
            COUNT(DISTINCT to_char(r.reading_datetime_utc AT TIME ZONE 'America/Chicago', 'YYYY-MM-DD')) AS days_reading_taken,
            MAX(p.insurance_identifier) AS insurance_identifier,
            MAX(l.date_created) AS last_reading_datetime,
            MAX(r.reading_datetime_utc) AS last_reading_timestamp,
            MAX(c.name) AS company_name,
            MAX(pn.phone) AS phone_number,
            MAX(con.address1) AS address1,
            MAX(con.address2) AS address2,
            MAX(con.city) AS city,
            MAX(con.state) AS state,
            MAX(con.zip) AS zip,
            MAX(p.gender) AS gender,
            MAX(p.date_of_birth) AS date_of_birth,
            MAX(d.meid) AS meid
        FROM auth_user u
            LEFT JOIN accounts_patientprofile p
                ON u.id = p.user_id
            LEFT JOIN readings_glucosereading r
                ON u.id = r.patient_id AND r.reading_datetime_utc BETWEEN %s AND %s
            LEFT JOIN gdrives_gdrive d
                ON d.patient_id = u.id
            LEFT JOIN gdrives_gdrivelogentry l
                ON l.reading_id = r.id
            LEFT JOIN accounts_company c
                ON p.company_id = c.id
            LEFT JOIN accounts_contact con
                ON p.contact_id = con.id
            LEFT JOIN accounts_phonenumber pn
                ON con.id = pn.contact_id
        WHERE p.id IS NOT NULL AND p.group_id = %s
        GROUP BY u.id
        """  # noqa
        total_days = int((end_plus - start).total_seconds() / 24 / 60 / 60)
        dt_format = '%Y-%m-%d 00:00:00 America/Chicago'
        start_date = start.strftime(dt_format)
        end_date = end_plus.strftime(dt_format)
        patients = User.objects.raw(query, [start_date, end_date, self.id])
        patient_count = 0
        tz = get_default_timezone()
        for patient in patients:
            patient_count += 1
            total_tests = patient.readings_taken
            days_tested = patient.days_reading_taken if total_tests > 0 else 0
            dt_format = "%m/%d/%y %I:%M:%S %p"
            if patient.last_reading_datetime:
                dt = make_naive(patient.last_reading_datetime, tz)
                dt_string = dt.strftime(dt_format)
            else:
                dt_string = "N/A"
            if patient.last_reading_timestamp:
                dt = make_naive(patient.last_reading_timestamp, tz)
                reading_dt_string = dt.strftime(dt_format)
            else:
                reading_dt_string = "N/A"
            account_created_string = patient.date_joined.strftime("%m/%d/%Y")
            account_age_days = (end - patient.date_joined.date()).days
            if patient.account_termination_date:
                account_terminated_string = \
                    patient.account_termination_date.strftime("%m/%d/%Y")
            else:
                account_terminated_string = "N/A"
            if self.is_no_pii:
                new_row = [
                    patient.company_name,
                    patient.epc_member_identifier,
                    patient.id,
                    patient.meid
                ]
            else:
                new_row = [
                    patient.company_name,
                    patient.first_name,
                    patient.last_name,
                    patient.insurance_identifier,
                    patient.epc_member_identifier,
                    patient.meid,
                    patient.address1,
                    patient.address2,
                    patient.city,
                    patient.state,
                    patient.zip,
                    patient.date_of_birth,
                    patient.gender,
                    patient.phone_number
                ]
            new_row.extend([
                account_created_string,
                account_age_days,
                patient.account_status,
                account_terminated_string,
                total_days,
                days_tested,
                round(float(total_tests) / days_tested, 2) if days_tested > 0
                else 0,
                round(100 * float(days_tested) / total_days, 2)
                if total_days > 0 else 0,
                total_tests,
                dt_string,
                reading_dt_string
            ])
            rows.append(new_row)

        output = io.StringIO()
        writer = csv.writer(output)
        # Write hreaders
        header_rows = [
            ['Title', 'Group Participation Report'],
            ['Date', '{} - {}'.format(start, end)],
            ['Group', self.name],
            ['Number of Patients', patient_count],
            [],
        ]
        if self.is_no_pii:
            header_rows.append([
                'Group',
                'EPC ID',
                'GHT ID',
                'MEID',
                'AccountCreated',
                'Account_Age',
                'Account Status',
                'Inactive Date',
                'Days',
                'Days Tested',
                'Avg Tests/Days Tested',
                '% Days Tested',
                'Total Tests',
                'Server Timestamp (CST)',
                'Reading Timestamp (CST)'
            ])
        else:
            header_rows.append([
                'Group',
                'First Name',
                'Last Name',
                'Insurance ID',
                'EPC ID',
                'MEID',
                'Address',
                'Address 2',
                'City',
                'State',
                'ZIP',
                'Date of Birth',
                'Gender',
                'Phone',
                'AccountCreated',
                'Account_Age',
                'Account Status',
                'Inactive Date',
                'Days',
                'Days Tested',
                'Avg Tests/Days Tested',
                '% Days Tested',
                'Total Tests',
                'Server Timestamp (CST)',
                'Reading Timestamp (CST)'
            ])
        for hr in header_rows:
            writer.writerow(hr)
        for row in rows:
            writer.writerow(row)
        content = output.getvalue()
        return content

    def generate_target_range_report(self, days: int) -> str:
        return _generate_target_range_report(
            self.get_patients().filter(patient_profile__account_status=PatientProfile.ACCOUNT_STATUS_ACTIVE),
            days,
            self.name,
            no_pii=self.is_no_pii
        )

    def get_available_devices(self, patient: Optional[User] = None, group_only: bool = False) -> 'QuerySet[GDrive]':
        """Get all devices that are available to patient, or in general if
        patient is not provided. If group_only == True, it will only include
        group devices, and not devices that are not assigned to any group."""
        queryset = self.get_devices(group_only).filter(
            last_assigned_patient=None, patient=None)
        # Devices associated with partners will never be available to patients
        # through MyGHR.
        queryset = queryset.filter(partner__isnull=True)
        if patient:
            queryset |= patient.previous_devices.all()
            current_device = patient.patient_profile.get_device()
            if current_device:
                queryset = queryset.exclude(pk=current_device.pk)
        return queryset

    def get_devices(self, group_only: bool = False) -> 'QuerySet[GDrive]':
        queryset = self.gdrives.all()
        if not group_only:
            queryset |= GDrive.objects.filter(group=None)
        return queryset

    def get_patients(self) -> 'QuerySet[User]':
        return User.objects.filter(patient_profile__in=self.patients.all())

    def get_professionals(self) -> 'QuerySet[User]':
        return User.objects.filter(professional_profile__in=self.professionals.all())

    def remove_patient(self, patient: User) -> None:
        profile: PatientProfile = patient.patient_profile
        profile.group = None
        profile.save()


class Payor(models.Model):
    name = models.CharField(max_length=100)
    contact = models.OneToOneField('Contact', on_delete=models.CASCADE)
    group = models.ForeignKey(GenesisGroup, related_name='payors', on_delete=models.CASCADE)

    class Meta:
        app_label = 'accounts'
        unique_together = ('name', 'group')

    def __str__(self) -> str:
        return self.name

    def get_patients(self) -> 'QuerySet[User]':
        company_ids = [
            int(i[0]) for i in self.companies.all().values_list('id')]
        return User.objects.filter(patient_profile__isnull=False).filter(
            patient_profile__company__pk__in=company_ids)


class Company(models.Model):
    BILLING_METHOD_MEDICAL = 'medical'
    BILLING_METHOD_PHARMACY = 'pharmacy'
    BILLING_METHOD_CHOICES = (
        (BILLING_METHOD_MEDICAL, 'Medical'),
        (BILLING_METHOD_PHARMACY, 'Pharmacy')
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

    name = models.CharField(max_length=100)
    contact = models.OneToOneField('Contact', on_delete=models.CASCADE)
    group = models.ForeignKey(
        GenesisGroup, related_name='companies', null=True, on_delete=models.SET_NULL)
    payor = models.ForeignKey(
        Payor, related_name='companies', null=True, blank=True, on_delete=models.SET_NULL)
    group_identifier = models.CharField(max_length=255, null=True, blank=True)
    billing_method = models.CharField(
        max_length=255, choices=BILLING_METHOD_CHOICES, null=True, blank=True)
    refill_method = models.CharField(
        max_length=255, choices=REFILL_METHOD_CHOICES, null=True, blank=True)
    start_kit_size = models.IntegerField(null=True, blank=True)
    minimum_refill_quantity = models.IntegerField(null=True, blank=True)
    bin_id = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="BIN")
    pcn_id = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="PCN")
    default_pharmacy = models.ForeignKey(
        'pharmacy.PharmacyPartner', related_name='companies', null=True,
        blank=True, on_delete=models.SET_NULL)
    glucose_strip_refill_frequency = models.PositiveIntegerField(
        null=True, blank=True)
    glucose_control_refill_frequency = models.PositiveIntegerField(
        null=True, blank=True)
    lancing_refill_frequency = models.PositiveIntegerField(
        null=True, blank=True)
    api_partner = models.ForeignKey(
        'api.APIPartner', related_name='companies', null=True, blank=True, on_delete=models.SET_NULL)
    nursing_group = models.ForeignKey(
        'nursing.NursingGroup', related_name='nursing_groups', null=True,
        blank=True, on_delete=models.SET_NULL)

    class Meta:
        app_label = 'accounts'
        unique_together = ('name', 'group')
        verbose_name_plural = "Companies"

    def __str__(self) -> str:
        return self.name
