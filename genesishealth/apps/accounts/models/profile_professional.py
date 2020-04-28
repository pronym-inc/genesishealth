from django.db import models, connection
from django.contrib.auth.models import User

from genesishealth.apps.accounts.password import make_password
from genesishealth.apps.accounts.reports import (
    _generate_noncompliance_report, _generate_target_range_report)

from .profile_base import BaseProfile


class ProfessionalProfile(BaseProfile):
    user = models.OneToOneField(User, related_name='professional_profile', on_delete=models.CASCADE)
    parent_group = models.ForeignKey(
        'GenesisGroup', related_name='professionals', on_delete=models.CASCADE)
    patients = models.ManyToManyField(
        'accounts.PatientProfile', related_name='professionals')
    watch_list = models.ManyToManyField(
        'accounts.PatientProfile', related_name='watch_list_professionals')

    class Meta:
        app_label = 'accounts'

    def __unicode__(self):
        return u"%s profile" % self.user.username

    def _get_business_partner(self):
        return self.parent_group

    def add_patient(self, patient):
        self.patients.add(patient.patient_profile)

    def remove_patient(self, patient):
        self.patients.remove(patient.patient_profile)

    def add_to_watch_list(self, patient):
        self.watch_list.add(patient.patient_profile)

    def remove_from_watch_list(self, patient):
        self.watch_list.remove(patient.patient_profile)

    def generate_standard_password(self):
        return make_password(self.user)

    def generate_noncompliance_report(self, hours, employer=None):
        patients = self.get_patients()
        if employer is not None:
            patients = patients.filter(patient_profile__company=employer)
        return _generate_noncompliance_report(
            patients,
            hours,
            "Patients for {}".format(self.user.get_full_name())
        )

    def generate_target_range_report(self, days, employer):
        patients = self.get_patients()
        if employer is not None:
            patients = patients.filter(patient_profile__company=employer)
        return _generate_target_range_report(
            patients,
            days,
            "Patients for {}".format(self.user.get_full_name())
        )

    def get_alerts(self):
        return self.user.created_professionalalerts.all()

    def get_patients(self):
        return User.objects.filter(patient_profile__in=self.patients.all())

    def get_patients_by_range(self, number_of_days=7, target='inside'):
        assert number_of_days in (1, 7, 14, 30, 60, 90)
        assert target in ('inside', 'above', 'below')
        if target == 'inside':
            query = """
                SELECT u.id FROM
                    auth_user u
                        LEFT JOIN health_information_healthprofessionaltargets h
                            ON (u.id = h.patient_id AND h.professional_id = %s)
                        LEFT JOIN accounts_patientprofile p ON u.id = p.user_id
                        LEFT JOIN accounts_patientstatisticrecord ps ON p.id = ps.profile_id
                WHERE ps.average_value_last_{0} IS NOT NULL AND (
                    h.id IS NOT NULL AND (
                        ps.average_value_last_{0} > h.premeal_glucose_goal_minimum
                        AND ps.average_value_last_{0} < h.postmeal_glucose_goal_maximum
                    )) OR (
                    h.ID IS NULL AND (
                        ps.average_value_last_{0} > 90
                        AND ps.average_value_last_{0} < 120
                    ))""".format(number_of_days)  # noqa
        elif target == 'below':
            query = """
                SELECT u.id FROM
                    auth_user u
                        LEFT JOIN health_information_healthprofessionaltargets h
                            ON (u.id = h.patient_id AND h.professional_id = %s)
                        LEFT JOIN accounts_patientprofile p ON u.id = p.user_id
                        LEFT JOIN accounts_patientstatisticrecord ps ON p.id = ps.profile_id
                WHERE ps.average_value_last_{0} IS NOT NULL AND (
                    h.id IS NOT NULL AND (
                        ps.average_value_last_{0} < h.premeal_glucose_goal_minimum
                    )) OR (
                    h.ID IS NULL AND (
                        ps.average_value_last_{0} < 90
                    ))""".format(number_of_days)  # noqa
        else:
            query = """
                SELECT u.id FROM
                    auth_user u
                        LEFT JOIN health_information_healthprofessionaltargets h
                            ON (u.id = h.patient_id AND h.professional_id = %s)
                        LEFT JOIN accounts_patientprofile p ON u.id = p.user_id
                        LEFT JOIN accounts_patientstatisticrecord ps ON p.id = ps.profile_id
                WHERE ps.average_value_last_{0} IS NOT NULL AND (
                    h.id IS NOT NULL AND (
                        ps.average_value_last_{0} > h.postmeal_glucose_goal_maximum
                    )) OR (
                    h.ID IS NULL AND (
                        ps.average_value_last_{0} > 120
                    ))""".format(number_of_days)  # noqa
        cursor = connection.cursor()
        cursor.execute(query, [self.user.pk])
        ids = map(lambda x: x[0], cursor.fetchall())
        return self.get_patients().filter(pk__in=ids)

    def get_patients_with_no_readings(self, number_of_days=7):
        assert number_of_days in (1, 7, 14, 30, 60, 90)
        query = """
            SELECT u.id FROM
                auth_user u
                    LEFT JOIN health_information_healthprofessionaltargets h
                        ON (u.id = h.patient_id AND h.professional_id = %s)
                    LEFT JOIN accounts_patientprofile p ON u.id = p.user_id
                    LEFT JOIN accounts_patientstatisticrecord ps ON p.id = ps.profile_id
            WHERE ps.readings_last_{0} IS NOT NULL
                AND ps.readings_last_{0} = 0""".format(number_of_days)  # noqa
        cursor = connection.cursor()
        cursor.execute(query, [self.user.pk])
        ids = map(lambda x: x[0], cursor.fetchall())
        return self.get_patients().filter(pk__in=ids)

    def get_in_compliance_patients(self, number_of_days=7):
        assert number_of_days in (1, 7, 14, 30, 60, 90)
        query = """
            SELECT u.id FROM
                auth_user u
                    LEFT JOIN health_information_healthprofessionaltargets h
                        ON (u.id = h.patient_id AND h.professional_id = %s)
                    LEFT JOIN accounts_patientprofile p ON u.id = p.user_id
                    LEFT JOIN accounts_patientstatisticrecord ps ON p.id = ps.profile_id
            WHERE ps.readings_last_{0} IS NOT NULL AND (
                    h.id IS NOT NULL AND ps.readings_last_{0} >= h.minimum_compliance
                ) OR (
                    h.ID IS NULL AND ps.readings_last_{0} >= 1
                )""".format(number_of_days)  # noqa
        cursor = connection.cursor()
        cursor.execute(query, [self.user.pk])
        ids = map(lambda x: x[0], cursor.fetchall())
        return self.get_patients().filter(pk__in=ids)

    def get_out_of_compliance_patients(self, number_of_days=7):
        assert number_of_days in (1, 7, 14, 30, 60, 90)
        query = """
            SELECT u.id FROM
                auth_user u
                    LEFT JOIN health_information_healthprofessionaltargets h
                        ON (u.id = h.patient_id AND h.professional_id = %s)
                    LEFT JOIN accounts_patientprofile p ON u.id = p.user_id
                    LEFT JOIN accounts_patientstatisticrecord ps ON p.id = ps.profile_id
            WHERE ps.readings_last_{0} IS NOT NULL AND (
                    h.id IS NOT NULL AND ps.readings_last_{0} < h.minimum_compliance
                ) OR (
                    h.ID IS NULL AND ps.readings_last_{0} < 1
                )""".format(number_of_days)  # noqa
        cursor = connection.cursor()
        cursor.execute(query, [self.user.pk])
        ids = map(lambda x: x[0], cursor.fetchall())
        return self.get_patients().filter(pk__in=ids)

    def get_out_of_range_patients(self, number_of_days=7):
        assert number_of_days in (1, 7, 14, 30, 60, 90)
        query = """
            SELECT u.id FROM
                auth_user u
                    LEFT JOIN health_information_healthprofessionaltargets h
                        ON (u.id = h.patient_id AND h.professional_id = %s)
                    LEFT JOIN accounts_patientprofile p ON u.id = p.user_id
                    LEFT JOIN accounts_patientstatisticrecord ps ON p.id = ps.profile_id
            WHERE ps.average_value_last_{0} IS NOT NULL AND (
                h.id IS NOT NULL AND (
                    ps.average_value_last_{0} < h.premeal_glucose_goal_minimum
                    OR ps.average_value_last_{0} > h.postmeal_glucose_goal_maximum
                )) OR (
                h.ID IS NULL AND (
                    ps.average_value_last_{0} < 90
                    OR ps.average_value_last_{0} > 120
                ))""".format(number_of_days)  # noqa
        cursor = connection.cursor()
        cursor.execute(query, [self.user.pk])
        ids = map(lambda x: x[0], cursor.fetchall())
        return self.get_patients().filter(pk__in=ids)

    def get_professionals_in_group(self):
        return self.parent_group.get_professionals()

    def get_unread_alert_notifications(self):
        return self.user.alert_notifications.filter(read=False)

    def get_watch_list(self):
        return User.objects.filter(patient_profile__in=self.watch_list.all())

    def save(self, *args, **kwargs):
        super(ProfessionalProfile, self).save(*args, **kwargs)
        # Make sure contact always stays up to date.
        shared_fields = ('first_name', 'last_name', 'email')
        for sf in shared_fields:
            setattr(self.contact, sf, getattr(self.user, sf))

        self.contact.save()

    def login_type(self):
        return 'Caregiver'
