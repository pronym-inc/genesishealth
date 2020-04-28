import random
from datetime import timedelta

from django.db import models
from django.contrib.auth.models import User
from django.db.models import IntegerField

from genesishealth.apps.utils.fields import SeparatedValuesField
from genesishealth.apps.utils.func import utcnow


class DemoPatientProfile(models.Model):
    READING_TYPE_GLUCOSE = 'glucose'
    READING_TYPE_WEIGHT = 'weight'
    READING_TYPE_BLOOD_PRESSURE = 'blood_pressure'
    READING_TYPE_EXERCISE = 'exercise'
    READING_TYPE_MEDICATION_EVENT = 'medication_event'
    READING_TYPE_MEAL = 'meal'

    READING_TYPE_CHOICES = (
        (READING_TYPE_GLUCOSE, 'Blood Glucose'),
        (READING_TYPE_WEIGHT, 'Weight'),
        (READING_TYPE_BLOOD_PRESSURE, 'Blood Pressure'),
        (READING_TYPE_EXERCISE, 'Exercise'),
        (READING_TYPE_MEDICATION_EVENT, 'Medication Event'),
        (READING_TYPE_MEAL, 'Meal')
    )

    GLUCOSE_READING_INTERVAL_WEEKLY = 'weekly'
    GLUCOSE_READING_INTERVAL_ONCE_DAILY = 'once_daily'
    GLUCOSE_READING_INTERVAL_THREE_TIMES_DAILY = 'three_times_daily'
    GLUCOSE_READING_INTERVAL_FIVE_TIMES_DAILY = 'five_times_daily'
    GLUCOSE_READING_INTERVAL_CHOICES = (
        (GLUCOSE_READING_INTERVAL_WEEKLY, 'Weekly'),
        (GLUCOSE_READING_INTERVAL_ONCE_DAILY, 'Once a day'),
        (GLUCOSE_READING_INTERVAL_THREE_TIMES_DAILY, 'Three times a day'),
        (GLUCOSE_READING_INTERVAL_FIVE_TIMES_DAILY, 'Five times a day')
    )

    user = models.OneToOneField(
        User, limit_choices_to={'patient_profile__isnull': False},
        related_name='demo_profile', on_delete=models.CASCADE)
    reading_types = SeparatedValuesField()
    glucose_reading_interval = models.CharField(
        max_length=100,
        choices=GLUCOSE_READING_INTERVAL_CHOICES,
        default=GLUCOSE_READING_INTERVAL_FIVE_TIMES_DAILY
    )
    average_premeal_glucose_level = models.IntegerField(default=100)
    average_postmeal_glucose_level = models.IntegerField(default=100)
    last_scheduled = models.DateTimeField(null=True)
    active = models.BooleanField(default=True)

    class Meta:
        app_label = 'accounts'

    @classmethod
    def convert_to_demo_patient(cls, patient, **kwargs):
        """Converts a normal patient to a demo patient."""
        patient.patient_profile.demo_patient = True
        patient.patient_profile.save()

        device = patient.patient_profile.get_device()
        if device:
            device.demo = True
            device.save()
        # Create a profile only if needed.
        try:
            patient.demo_profile
        except DemoPatientProfile.DoesNotExist:
            DemoPatientProfile.objects.create(user=patient, **kwargs)

    def cron_process(self):
        self.schedule()
        for sdr in self.user.scheduled_demo_readings.filter(
                fired=False, reading_datetime__lt=utcnow()):
            if self.user.patient_profile.get_device():
                sdr.process()

    def check_schedule_ok(self):
        return (self.last_scheduled is not None and
                (utcnow() - self.last_scheduled <
                    (timedelta(days=7) - timedelta(hours=1))))

    def generate_glucose_value(self, premeal):
        if premeal:
            start = self.average_premeal_glucose_level
        else:
            start = self.average_postmeal_glucose_level
        return random.randint(start - 30, start + 30)

    def schedule(self):
        if self.check_schedule_ok():
            return
        glucose_reading_times = []
        if (self.glucose_reading_interval ==
                DemoPatientProfile.GLUCOSE_READING_INTERVAL_WEEKLY):
            glucose_reading_times.append(utcnow() + timedelta(
                seconds=random.randint(0, 60 * 60 * 24 * 7)))
        elif (self.glucose_reading_interval ==
                DemoPatientProfile.GLUCOSE_READING_INTERVAL_ONCE_DAILY):
            for i in range(7):
                glucose_reading_times.append(
                    utcnow() + timedelta(days=i) +
                    timedelta(seconds=random.randint(0, 60 * 60 * 24)))
        elif self.glucose_reading_interval in (
                DemoPatientProfile.GLUCOSE_READING_INTERVAL_THREE_TIMES_DAILY,
                DemoPatientProfile.GLUCOSE_READING_INTERVAL_FIVE_TIMES_DAILY):
            if (self.glucose_reading_interval ==
                    DemoPatientProfile
                    .GLUCOSE_READING_INTERVAL_THREE_TIMES_DAILY):
                day_segments = 3
            else:
                day_segments = 5
            day_portion = 60 * 60 * 24 / day_segments
            for i in range(7):
                for j in range(day_segments):
                    glucose_reading_times.append(
                        utcnow() + timedelta(days=i) +
                        timedelta(
                            seconds=((j * day_portion) +
                                     random.randint(0, day_portion))))
        for grt in glucose_reading_times:
            DemoScheduledReading.generate_scheduled_reading(
                self.user, grt, random.choice([True, False]))
        self.last_scheduled = utcnow()
        self.save()

    def login_type(self):
        return "Demo Patient"


class DemoScheduledReading(models.Model):
    patient = models.ForeignKey(
        User,
        limit_choices_to={'patient_profile__isnull': False,
                          'patient_profile__demo_patient': True},
        related_name='scheduled_demo_readings', on_delete=models.CASCADE)
    value = models.IntegerField()
    reading_datetime = models.DateTimeField()
    fired = models.BooleanField(default=False)
    premeal = models.BooleanField()
    response = models.TextField(null=True)

    class Meta:
        app_label = 'accounts'

    @classmethod
    def generate_scheduled_reading(cls, patient, in_datetime, premeal):
        glucose_value = patient.demo_profile.generate_glucose_value(premeal)
        reading = cls(
            patient=patient, value=glucose_value,
            reading_datetime=in_datetime, premeal=premeal)
        reading.save()
        return reading

    def process(self, force=False):
        if (self.fired or
                (self.reading_datetime > utcnow() and not force) or
                not self.patient.patient_profile.get_device()):
            return
        self.patient.patient_profile.send_http_reading()
        self.response = ''
        self.fired = True
        self.save()
