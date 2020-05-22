from datetime import timedelta
import logging

from django.db import models
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.conf import settings

from genesishealth.apps.utils.sms import send_text_message
from genesishealth.apps.utils.func import utcnow

alert_logger = logging.getLogger('alerts')


class BaseAlert(models.Model):
    class Meta:
        abstract = True

    READING_RECEIVED = 'reading_received'

    TYPE_CHOICES = (
        (READING_RECEIVED, 'Reading Received'),
    )

    CANNED_MESSAGES = {
        READING_RECEIVED: {
            'patient': (
                '%(patient)s took a blood glucose reading '
                'at %(time)s with a value of %(value)s.'),
            'other': (
                '%(patient)s took a blood glucose reading '
                'at %(time)s with a value of %(value)s.')
        }
    }

    CANNED_SUBJECTS = {
        READING_RECEIVED: {
            'patient': '%(patient)s took a glucose reading.',
            'other': '%(patient)s took a glucose reading.'
        }
    }

    patient = models.ForeignKey(User, related_name='my_%(class)ss', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    type = models.CharField(
        max_length=40,
        choices=TYPE_CHOICES,
        default=READING_RECEIVED)
    active = models.BooleanField(default=True)
    last_triggered = models.DateTimeField(null=True)
    created_by = models.ForeignKey(User, related_name='created_%(class)ss', on_delete=models.CASCADE)

    def __str__(self) -> str:
        return u"%s" % self.name

    def render_subject(self, to_patient, **details):
        details['patient'] = self.patient.first_name
        recipient = 'patient' if to_patient else 'other'
        subject_format = self.CANNED_SUBJECTS[self.type][recipient]
        subject = subject_format % details
        return subject

    def render_message(self, to_patient, **details):
        details['patient'] = self.patient.first_name
        recipient = 'patient' if to_patient else 'other'
        message_format = self.CANNED_MESSAGES[self.type][recipient]
        message = message_format % details
        return message

    def trigger(self, **details):
        from genesishealth.apps.alerts.tasks import trigger_alert
        trigger_alert.delay(self, **details)

    def trigger_delayed(self, commit=True, **details):
        self.send_texts(**details)
        self.send_emails(**details)
        self.last_triggered = utcnow()
        if commit:
            self.save()


class ProfessionalAlert(BaseAlert):
    """An alert created by a professional."""
    OUT_OF_TARGET_COMPLIANCE = 'out_of_target_compliance'
    OUT_OF_MINIMUM_COMPLIANCE = 'out_of_minimum_compliance'
    GLUCOSE_DANGER_RANGE = 'glucose_danger_range'
    GLUCOSE_OUT_OF_RANGE = 'glucose_out_of_range'
    REMINDER = 'reminder'

    # Add in the new types of readings professionals have access to.
    TYPE_CHOICES = list(BaseAlert.TYPE_CHOICES)
    TYPE_CHOICES.extend([
        (OUT_OF_TARGET_COMPLIANCE, 'Out of Target Compliance'),
        (OUT_OF_MINIMUM_COMPLIANCE, 'Out of Minimum Compliance'),
        (GLUCOSE_DANGER_RANGE, 'Glucose Level in Danger Range'),
        (GLUCOSE_OUT_OF_RANGE, 'Glucose Level out of Target Range')
    ])
    TYPE_CHOICES = tuple(TYPE_CHOICES)

    PROFESSIONAL_RECIPIENT = 'professional_recipient'
    PATIENT_RECIPIENT = 'patient_recipient'
    OTHER_RECIPIENT = 'other_recipient'
    RECIPIENT_TYPE_CHOICES = (
        (PROFESSIONAL_RECIPIENT, 'Professional'),
        (PATIENT_RECIPIENT, 'Patient')
    )

    TEXT_CONTACT = 'send_by_text'
    EMAIL_CONTACT = 'send_by_email'
    MESSAGE_CONTACT = 'send_by_message'
    APP_CONTACT = 'send_by_app'
    CONTACT_METHODS = [TEXT_CONTACT, EMAIL_CONTACT, APP_CONTACT]
    if settings.ENABLE_PHONE_APP_FOR_ALERTS:
        CONTACT_METHODS.append(APP_CONTACT)

    CANNED_MESSAGES = BaseAlert.CANNED_MESSAGES.copy()
    CANNED_MESSAGES.update({
        OUT_OF_TARGET_COMPLIANCE: {
            'patient': (
                'You have fallen below the target compliance level '
                'of %(compliance_target)s readings per day.'),
            'other': (
                '%(patient)s has fallen below the target compliance level '
                'of %(compliance_target)s readings per day.')
        },
        OUT_OF_MINIMUM_COMPLIANCE: {
            'patient': (
                'You have fallen below the minimum compliance level of '
                '%(compliance_target)s readings per day.'),
            'other': (
                '%(patient)s has fallen below the minimum compliance '
                'level of %(compliance_target)s readings per day.')
        },
        GLUCOSE_DANGER_RANGE: {
            'patient': (
                'Your blood glucose level of %(value)s is outside of the '
                'safe range.  Please seek medical attention.'),
            'other': (
                '%(patient)s\'s blood glucose level of %(value)s is outside '
                'of the safe range.')
        },
        GLUCOSE_OUT_OF_RANGE: {
            'patient': (
                'Your blood glucose level of %(value)s is outside of '
                'your target range.'),
            'other': (
                '%(patient)s\'s blood glucose level of %(value)s is outside '
                'of his/her target range.')
        }
    })

    CANNED_SUBJECTS = BaseAlert.CANNED_SUBJECTS.copy()
    CANNED_SUBJECTS.update({
        OUT_OF_TARGET_COMPLIANCE: {
            'patient': 'You have fallen below your compliance goal.',
            'other': '%(patient)s has fallen below his/her compliance goal.'
        },
        OUT_OF_MINIMUM_COMPLIANCE: {
            'patient': 'You have fallen out of compliance',
            'other': '%(patient)s has fallen out of compliance.'
        },
        GLUCOSE_DANGER_RANGE: {
            'patient': 'You took a glucose reading with a dangerous value.',
            'other': (
                '%(patient)s took a glucose reading with a dangerous value.'),
        },
        GLUCOSE_OUT_OF_RANGE: {
            'patient': (
                'Your average daily glucose value is outside of your ideal '
                'range.'),
            'other': (
                '%(patient)s\'s average daily glucose value was outside of '
                'his/her ideal range.')
        }
    })

    group = models.ForeignKey(
        'accounts.GenesisGroup',
        null=True,
        related_name='alerts',
        on_delete=models.CASCADE)
    message = models.TextField(default="")
    recipient_type = models.CharField(
        max_length=100,
        choices=RECIPIENT_TYPE_CHOICES)
    professionals = models.ManyToManyField(User, related_name='alerts')
    send_by_text = models.BooleanField(default=False)
    send_by_email = models.BooleanField(default=False)
    send_by_app = models.BooleanField(default=False)
    template = models.ForeignKey('AlertTemplate', null=True, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return u"%s" % self.name

    def render_message(self, to_patient, **details):
        message = super(ProfessionalAlert, self).render_message(
            to_patient, **details)
        message += '\n\n' + self.message
        return message

    def send_emails(self, **details):
        if not self.send_by_email:
            return
        is_pa = self.recipient_type == ProfessionalAlert.PATIENT_RECIPIENT
        message = self.render_message(is_pa, **details)
        subject = self.render_subject(is_pa, **details)

        if self.recipient_type == ProfessionalAlert.PATIENT_RECIPIENT:
            self.patient.patient_profile.send_email(subject, message)
        elif self.recipient_type == ProfessionalAlert.PROFESSIONAL_RECIPIENT:
            for prof in self.professionals.all():
                prof.professional_profile.send_email(subject, message)
        else:
            raise Exception('Unknown recipient type')

    def send_messages(self, **kwargs):
        if self.recipient_type == ProfessionalAlert.PROFESSIONAL_RECIPIENT:
            for u in self.professionals.all():
                notification = AlertNotification(alert=self, user=u)
                notification.save()

    def send_texts(self, **details):
        if not self.send_by_text:
            return
        is_pa = self.recipient_type == ProfessionalAlert.PATIENT_RECIPIENT
        message = self.render_message(is_pa, **details)

        if self.recipient_type == ProfessionalAlert.PATIENT_RECIPIENT:
            self.patient.patient_profile.send_text(message)
        elif self.recipient_type == ProfessionalAlert.PROFESSIONAL_RECIPIENT:
            for prof in self.professionals.all():
                prof.professional_profile.send_text(message)

    def trigger_delayed(self, **details):
        super(ProfessionalAlert, self).trigger_delayed(commit=False, **details)
        self.send_messages()
        self.save()

    def trigger_if_ready(self):
        """Note that this will only work on the "scheduled"/"regular" triggers.
          E.g. it will not work on reading received alerts."""
        if self.type in (
                ProfessionalAlert.READING_RECEIVED,
                ProfessionalAlert.GLUCOSE_DANGER_RANGE):
            raise Exception(
                'trigger_if_ready should not be called on reading received '
                'or danger range alerts.')
        # Only proceed if triggered is empty orwas more than a weak ago.
        if (self.last_triggered is not None and
                self.last_triggered + timedelta(days=7) > utcnow()):
            return
        patient_name = self.patient.first_name
        healthinformation = self.patient.healthinformation
        if self.type == ProfessionalAlert.OUT_OF_TARGET_COMPLIANCE:
            compliance_goal = self.patient.healthinformation.compliance_goal
            if (self.patient.patient_profile.get_average_daily_readings() <
                    compliance_goal):
                self.trigger(
                    compliance_target=healthinformation.compliance_goal,
                    patient=patient_name)
        elif self.type == ProfessionalAlert.OUT_OF_MINIMUM_COMPLIANCE:
            if (self.patient.patient_profile.get_average_daily_readings() <
                    healthinformation.minimum_compliance):
                self.trigger(
                    compliance_target=healthinformation.minimum_compliance,
                    patient=patient_name)
        elif self.type == ProfessionalAlert.GLUCOSE_OUT_OF_RANGE:
            avg = self.patient.patient_profile.get_average_glucose_level()
            if (avg < healthinformation.premeal_glucose_goal_minimum or
                    avg > healthinformation.postmeal_glucose_goal_maximum):
                self.trigger(
                    value=avg,
                    patient=patient_name)


class PatientAlert(BaseAlert):
    phone_number = models.CharField(max_length=100, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)

    def log(self, type_, success, recipient):
        PatientAlertNotificationLogEntry(
            alert=self,
            type=type_,
            success=success,
            recipient=recipient).save()

    def send_emails(self, **details):
        if not self.email or settings.DISABLE_ALERTS:
            return
        message = self.render_message(True, **details)
        subject = self.render_subject(True, **details)

        message = EmailMessage(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.DEFAULT_FROM_EMAIL, ],
            [self.email])
        success = True
        try:
            message.send()
        except:
            success = False
        self.log(
            success=success,
            type_=PatientAlertNotificationLogEntry.TYPE_CHOICE_EMAIL,
            recipient=self.email)

    def send_texts(self, **details):
        if settings.DISABLE_ALERTS:
            return
        alert_logger.info('In send_texts: %s' % (repr(self)))
        if not self.phone_number:
            return
        message = self.render_message(True, **details)
        success = bool(send_text_message(self.phone_number, message))
        self.log(
            success=success,
            type_=PatientAlertNotificationLogEntry.TYPE_CHOICE_TEXT,
            recipient=self.phone_number)


class AlertTemplate(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(
        max_length=40, choices=ProfessionalAlert.TYPE_CHOICES)
    message = models.TextField(default="")
    recipient_type = models.CharField(
        max_length=100, choices=ProfessionalAlert.RECIPIENT_TYPE_CHOICES)
    group = models.ForeignKey(
        'accounts.GenesisGroup', related_name='alert_templates', on_delete=models.CASCADE)
    enabled = models.BooleanField(default=True)
    send_by_text = models.BooleanField(default=False)
    send_by_email = models.BooleanField(default=False)
    send_by_message = models.BooleanField(default=True)
    send_by_app = models.BooleanField(default=True)

    class Meta:
        unique_together = ('name', 'group')

    def __str__(self) -> str:
        return self.name


def readable_type(self):
    for k, v in ProfessionalAlert.TYPE_CHOICES:
        if self.type == k:
            return v
    return None


def readable_recipient_type(self):
    for k, v in ProfessionalAlert.RECIPIENT_TYPE_CHOICES:
        if self.recipient_type == k:
            return v
    return None

ProfessionalAlert.readable_type = AlertTemplate.readable_type = readable_type
ProfessionalAlert.readable_recipient_type = readable_recipient_type
AlertTemplate.readable_recipient_type = readable_recipient_type


class AlertNotification(models.Model):
    alert = models.ForeignKey(ProfessionalAlert, related_name='alerts', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='alert_notifications', on_delete=models.CASCADE)
    read = models.BooleanField(default=False)
    sent_on = models.DateTimeField(auto_now_add=True)


class PatientAlertNotificationLogEntry(models.Model):
    """Log entry for either a text message or email."""
    TYPE_CHOICE_EMAIL = 'email'
    TYPE_CHOICE_TEXT = 'text'
    TYPE_CHOICES = (
        (TYPE_CHOICE_EMAIL, 'Email'),
        (TYPE_CHOICE_TEXT, 'Text'),
    )
    alert = models.ForeignKey(PatientAlert, on_delete=models.CASCADE)
    type = models.CharField(max_length=255, choices=TYPE_CHOICES)
    # Email or phone number being sent to.
    recipient = models.CharField(max_length=255)
    datetime_created = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField()
