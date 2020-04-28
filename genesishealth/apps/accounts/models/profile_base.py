from datetime import timedelta, datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from django.core.mail import EmailMessage
from django.db import models
from django.db.models.query import QuerySet
from django.template.loader import render_to_string

from genesishealth.apps.accounts.password import make_password
from genesishealth.apps.utils.func import (
    filter_dict_to_model_fields, utcnow, compare_phone_numbers)

import pytz

from .contact import Contact
from .message import Message, MessageEntry


SECURITY_QUESTIONS = (
    ("grade_school", "What Grade School did you attend?"),
    ("mother_maiden", "What is your mother's Maiden name?"),
    ("grandmother_madien", "What is your paternal grandmother's maiden name?"),
    ("street", "What Street did you grow up on?"),
    ("eldest_sibling", "In what year was your eldest sibling born?"),
    ("hs_mascot", "What was the name of your high school mascot?"),
    ("favorite_pet", "What is the name of your favorite pet?"),
    ("favorite_food", "What is your favorite food?"),
    ("city_born", "In what city where you born?"),
)


class LoginRecord(models.Model):
    """Record that a user logged in."""
    user = models.ForeignKey(User, related_name='login_records', on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'accounts'


class ProfileQuerySet(QuerySet):
    """Custom queryset for profiles."""
    def update(self, *args, **kwargs):
        # Get related name
        related_name = self.model._meta.get_field('user').related_query_name()
        # Pull in users
        user_kwargs = {'%s__in' % related_name: self}
        users = User.objects.filter(**user_kwargs)
        record_count = users.update(
            **filter_dict_to_model_fields(kwargs, User))
        # Pull in and update contacts
        contacts = Contact.objects.filter(pk__in=self.values('contact'))
        record_count += contacts.update(
            **filter_dict_to_model_fields(kwargs, Contact))
        # Update profile.
        record_count += super(ProfileQuerySet, self).update(
            **filter_dict_to_model_fields(kwargs, self.model))
        return record_count


class ProfileManager(models.Manager):
    """Manager for profiles."""
    def create_profile(self, user, **kwargs):
        contact = Contact.objects.create(
            **filter_dict_to_model_fields(kwargs, Contact))
        contact.save()

        profile = self.model(
            user=user, contact=contact,
            **filter_dict_to_model_fields(kwargs, self.model))
        profile.save()

        return profile

    def create_user(self, username, email, password=None,
                    email_password=True, **kwargs):
        """Creates a user with the proper profile."""
        if password is None:
            password = make_password()
        user = User.objects.create_user(username, email, password)
        for k, v in filter_dict_to_model_fields(kwargs, User).items():
            setattr(user, k, v)
        user.save()
        self.create_profile(user, **kwargs)
        if email_password:
            user.get_profile().email_password(password)
        return user

    def generate_username(self, seed):
        """Generates a unique username from seed."""
        test_username = seed
        count = 1
        while True:
            try:
                User.objects.get(username=test_username)
            except User.DoesNotExist:
                return test_username
            test_username = '%s%s' % (seed, count)
            count += 1

    def get_queryset(self):
        return ProfileQuerySet(self.model)

    def get_users(self):
        """Get User objects associated with this profile type."""
        related_name = self.model._meta.get_field('user').related_query_name()
        kwargs = {'%s__isnull' % related_name: False}
        return User.objects.filter(**kwargs)


class BaseProfile(models.Model):
    # American timezones
    ALLOWED_TIMEZONES = [
        (tz, tz) for tz in pytz.all_timezones if tz.startswith("US/")]

    contact = models.OneToOneField('Contact', related_name='+', on_delete=models.CASCADE)
    last_touched = models.DateTimeField(null=True)
    forgot_key = models.CharField(
        blank=True, max_length=40, editable=False, null=True)
    forgot_key_updated = models.DateTimeField(
        blank=True, editable=False, null=True)
    email_update_new = models.EmailField(blank=True, editable=False, null=True)
    email_update_key = models.CharField(
        blank=True, max_length=40, editable=False, null=True)
    email_update_key_updated = models.DateTimeField(
        blank=True, editable=False, null=True)
    timezone_name = models.CharField(
        max_length=255, choices=ALLOWED_TIMEZONES, default="US/Central")
    security_question1 = models.CharField(
        blank=True, choices=SECURITY_QUESTIONS, max_length=100, null=True)
    security_answer1 = models.CharField(blank=True, max_length=100, null=True)
    security_question2 = models.CharField(
        blank=True, choices=SECURITY_QUESTIONS, max_length=100, null=True)
    security_answer2 = models.CharField(blank=True, max_length=100, null=True)
    security_question3 = models.CharField(
        blank=True, choices=SECURITY_QUESTIONS, max_length=100, null=True)
    security_answer3 = models.CharField(blank=True, max_length=100, null=True)
    configured = models.BooleanField(default=False, editable=False)
    is_reset_password = models.BooleanField(default=False, editable=False)
    is_accepted_terms = models.BooleanField(default=False, editable=False)
    is_accepted_privacy = models.BooleanField(default=False, editable=False)

    objects = ProfileManager()

    class Meta:
        app_label = 'accounts'
        abstract = True

    @classmethod
    def get_logged_in_users(cls):
        login_records = LoginRecord.objects.filter(
            datetime__gt=(
                utcnow() - timedelta(seconds=settings.LOGGED_IN_TIME)))
        # Get profiles first so we're not included users
        # without this kind of profile.
        profiles = cls.objects.filter(
            user__pk__in=login_records.values_list('user'))
        users = User.objects.filter(pk__in=profiles.values_list('user'))
        return users

    def email_password(self, password,
                       template='accounts/create_new_password.txt'):
        """
        Emails the user their password.  Note, password must be provided,
        since they are not saved in the database.
        """
        message = render_to_string(template, {
            'name': self.user.get_full_name(),
            'site_url': settings.SITE_URL,
            'password': password
        })
        self.send_email(
            'MyGHR temporary password for {}'.format(
                self.user.get_full_name()),
            message
        )

    def get_last_login(self):
        """Usually you actually want second to last, because
        you want the previous one to the login that just
        happened."""
        logins = self.user.login_records.order_by('-datetime')
        if logins.count() > 1:
            return logins[1]

    def get_message_entries(self):  # pragma: no cover
        return MessageEntry.objects.filter(recipient=self.user)

    def get_number_of_logins(self):
        return self.user.login_records.all().count()

    def get_readable_security_questions(self):
        questions = []
        for i in range(1, 4):
            sq = getattr(self, 'security_question%s' % i)
            sa = getattr(self, 'security_answer%s' % i)
            hr_question = None
            for question in SECURITY_QUESTIONS:
                if sq == question[0]:
                    hr_question = question[1]
            questions.append({'question': hr_question, 'answer': sa})
        return questions

    def get_security_question_choices(self):
        """Returns a choices-compatible tuple of security questions."""
        questions = []
        for i in range(1, 4):
            question = getattr(self, 'security_question{0}'.format(i))
            readable = getattr(
                self, 'get_security_question{0}_display'.format(i))()
            questions.append((question, readable))
        return tuple(questions)

    def get_sent_messages(self):  # pragma: no cover
        return Message.objects.filter(sender=self.user)

    def get_timezone_offset(self, dt=None):
        """Returns timezone offset in hours."""
        if dt is None:
            dt = datetime.now()
        offset = self.timezone.utcoffset(dt)
        return int(offset.total_seconds() / 60 / 60)

    def get_unread_messages(self):  # pragma: no cover
        return Message.objects.filter(
            id__in=MessageEntry.objects.filter(
                recipient=self.user, read=False
            ).order_by('-message__sent_at').values_list('message')
        )

    def handle_login(self):
        LoginRecord(user=self.user).save()

    def has_phone_number(self, phone_number):
        """Returns whether or not user has the provided phone number."""
        for pn in self.contact.phonenumber_set.all():
            if compare_phone_numbers(phone_number, pn.phone):
                return True
        return False

    def is_logged_in(self):
        idle_timedelta = utcnow() - self.last_touched
        idle_time = idle_timedelta.total_seconds()
        return idle_time < settings.LOGGED_IN_TIME

    def logins_since(self, since):
        return self.user.login_records.filter(datetime__gte=since)

    def reset_password(self, password=None, email=True):
        """Resets the user's password and emails them their password."""
        self.is_reset_password = True
        self.save()
        if password is None:
            password = make_password(self.user)
        self.user.set_password(password)
        self.user.save()
        if email:
            self.email_password(
                password, template='accounts/reset_password.txt')

    def send_email(self, subject, message):
        if not settings.SEND_EMAILS:
            return
        if self.user.email:
            message = EmailMessage(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.DEFAULT_FROM_EMAIL],
                [self.user.email]
            )
            message.send()

    def set_standard_password(self, email=True):
        self.reset_password(
            password=self.generate_standard_password(),
            email=email
        )

    def touch(self, commit=True):
        self.last_touched = utcnow()
        if commit:
            self.save()

    def update(self, save=False, **kwargs):
        """Method updates a patient provided a dictionary of new items."""
        for obj in (self, self.user, self.contact):
            fkwargs = filter_dict_to_model_fields(kwargs, obj)
            for key, value in fkwargs.items():
                setattr(obj, key, value)
            if save:
                obj.save()

    def verify_security_question(self, question, answer):
        """Verifies that the given answer is correct for the
        security question provided."""
        for i in range(1, 4):
            if question == getattr(self, 'security_question{0}'.format(i)):
                cleaned_answer = getattr(
                    self, 'security_answer{0}'.format(i)).lower()
                return answer.lower() == cleaned_answer
        raise Exception('User does not have that question.')

    @property
    def timezone(self):
        return pytz.timezone(self.timezone_name)

    @property
    def business_partner(self):
        return self._get_business_partner()


# Connect a signal to update some info when the user logs in.
def handle_login(sender, user, request, **kwargs):
    try:
        profile = user.get_profile()
    except:
        try:
            admin_profile = user.admin_profile
        except:
            pass
        else:
            admin_profile.handle_login()
    else:
        profile.handle_login()

user_logged_in.connect(handle_login)


class Note(models.Model):
    patient = models.ForeignKey(
        User,
        limit_choices_to={'patient_profile__isnull': False},
        related_name='notes_about', on_delete=models.CASCADE)
    author = models.ForeignKey(
        User,
        limit_choices_to={'professional_profile__isnull': False},
        related_name='notes_authored', on_delete=models.CASCADE)
    content = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'accounts'

    def update(self, content):
        self.content = content
        self.save()


class PreviousPassword(models.Model):
    user = models.ForeignKey('auth.User', related_name='previous_passwords', on_delete=models.CASCADE)
    password = models.CharField(max_length=255)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-date_added',)
