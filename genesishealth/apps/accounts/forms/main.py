from collections import OrderedDict
from dateutil.relativedelta import relativedelta
from hashlib import sha1 as sha_constructor
import random

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils.timezone import now

from genesishealth.apps.accounts.models import (
    PatientProfile, ProfessionalProfile, SECURITY_QUESTIONS)
from genesishealth.apps.accounts.password import (
    set_password, validate_password)
from genesishealth.apps.utils.forms import (
    SinglePhoneField, SecurityQuestionWidget, GenesisForm, GenesisModelForm)
from genesishealth.apps.utils.func import utcnow


INSURANCE_TYPE_CHOICES = (
    ('TRADITIONAL', 'TRADITIONAL'),
    ('SELF-FUNDED', 'SELF-FUNDED'),
    ('DOCTOR', 'DOCTOR'),
    ('PHARMACIST', 'PHARMACIST')
)

PASSWORD_HELP_TEXT = (
    "Your password must be at least eight characters long and contain at least"
    " one number (0-9), one capital letter, and at least one special "
    "character: !@#$%^&*()")


class VerifyPasswordMixin(object):
    """
    Mixin that validates current_password
    """
    def clean_current_password(self):
        password = self.cleaned_data.get('current_password')
        if not self.user.check_password(password):
            raise forms.ValidationError(
                "Please enter a correct current password.")
        return None


class VerifyPhoneMixin(object):
    def clean_verify_phone(self):
        user = getattr(self, 'user', None)
        if user is not None and not user.get_profile().has_phone_number(
                self.cleaned_data['verify_phone']):
            raise forms.ValidationError(
                "The phone number that you entered doesn't "
                "belong to the specified user.")
        return None


class VerifyNewPasswordMixin(object):
    def verify_passwords(self):
        data = self.cleaned_data
        if 'password' in data and data['confirm_password'] != data['password']:
            raise forms.ValidationError('Passwords do not match.')

    def clean_password(self):
        password = self.cleaned_data['password']
        try:
            validate_password(self.user, password)
        except AssertionError as e:
            raise forms.ValidationError(str(e))
        return password


class SecurityQuestionsMixin(object):
    def clean_security_question2(self):
        sq2 = self.cleaned_data['security_question2']
        sq1 = self.cleaned_data['security_question1']
        if sq2 == sq1:
            raise forms.ValidationError("Please choose a different question.")
        return sq2

    def clean_security_question3(self):
        sq3 = self.cleaned_data['security_question3']
        if sq3 in (self.cleaned_data['security_question1'],
                   self.cleaned_data.get('security_question2')):
            raise forms.ValidationError("Please choose a different question.")
        return sq3


class AnswerSecurityQuestionMixin(object):
    def __init__(self, *args, **kwargs):
        user = getattr(self, 'user', None)
        if user is not None:
            question_no = random.choice(range(1, 4))
            # Sending just the number of the question, because that's enough to
            # retrieve the corresponding stored answer
            self.fields['question'].initial = question_no

            # Setting the full text of the security question
            self.fields['security_question'].initial = self._get_full_question(
                user.get_profile(),
                question_no
            )

        elif self.is_bound:
            # Because the `security_question` field is not a real form field,
            # we have to populate it here, so that it shows up in case the form
            # validation fails and the form is displayed again with the error
            print(self.data)
            question_no = self.data['question']
            try:
                user = User.objects.get(username=self.data['username'])
            except User.DoesNotExist:
                full_question = 'No question available.'
            else:
                full_question = self._get_full_question(
                    user.get_profile(), question_no)
                # Making the data dict mutable, so that we can add the
                # text of the security question to it
            self.data = self.data.copy()
            self.data['security_question'] = full_question

    def _get_full_question(self, profile, question_no):
        """
        Returns the full text of the question identified by `question_no`
        and which belongs to `self.profile`
        """
        question = getattr(profile, 'security_question%s' % question_no)
        try:
            return dict(SECURITY_QUESTIONS)[question]
        except KeyError:
            pass

    def clean_answer(self):
        user = getattr(self, 'user', None)
        if user is not None:
            question_no = self.cleaned_data['question']
            question = getattr(
                user.get_profile(), 'security_question%s' % question_no)
            answer = self.cleaned_data['answer']
            if not user.get_profile().verify_security_question(
                    question, answer):
                raise forms.ValidationError(
                    "The answer you gave is incorrect.")
        return self.cleaned_data['answer']


class AuthenticationForm(forms.Form):
    """
    Base class for authenticating users. Extend this to get a form that accepts
    username/password logins.
    """
    username = forms.CharField(label="Username", max_length=255)
    password = forms.CharField(label="Password", widget=forms.PasswordInput)

    error_messages = {
        'auth_failed': "Please enter a correct username and password. Note "
                       "that both fields are case-sensitive.",
        'inactive_user': "This account is inactive.",
        'no_cookies': "Your Web browser doesn't appear to have cookies "
                      "enabled. Cookies are required for logging in.",
    }

    def __init__(self, request=None, *args, **kwargs):
        """
        If request is passed in, the form will validate that cookies are
        enabled. Note that the request (a HttpRequest object) must have set a
        cookie with the key TEST_COOKIE_NAME and value TEST_COOKIE_VALUE before
        running this validation.
        """
        self.request = request
        self.user_cache = None
        super(AuthenticationForm, self).__init__(*args, **kwargs)

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(
                username=username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(self.error_messages['auth_failed'])
            elif not self.user_cache.is_active:
                raise forms.ValidationError(
                    self.error_messages['inactive_user'])
        return self.cleaned_data

    def check_for_test_cookie(self):
        if self.request and not self.request.session.test_cookie_worked():
            raise forms.ValidationError(self.error_messages['no_cookies'])

    def get_user_id(self):
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self):
        return self.user_cache


class UpdateEmailForm(GenesisForm):
    current_password = forms.CharField(
        max_length=100,
        widget=forms.PasswordInput(attrs={'class': 'required'}))
    email = forms.EmailField(
        widget=forms.TextInput(attrs={'class': 'required'}))
    confirm_email = forms.EmailField(
        widget=forms.TextInput(attrs={'class': 'required'}))

    error_messages = {
        'email_exists': "The provided email address is already in use. Please "
                        "provide another one.",
        'email_mismatch': "The provided emails do not match.",
        'wrong_password': 'Provided password is incorrect.'
    }

    def __init__(self, *args, **kwargs):
        self.user = kwargs['user']
        del kwargs['user']
        super(UpdateEmailForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            User.objects.exclude(pk=self.user.id).get(
                Q(email=email) | Q(username=email))
        except User.DoesNotExist:
            pass
        else:
            print('wtf')
            raise forms.ValidationError(self.error_messages['email_exists'])

        return email

    def clean_confirm_email(self):
        confirm_email = self.cleaned_data.get('confirm_email')
        email = self.cleaned_data.get('email')
        if email and confirm_email != email:
            raise forms.ValidationError(self.error_messages['email_mismatch'])
        return confirm_email

    def clean_current_password(self):
        if not self.user.check_password(self.cleaned_data['current_password']):
            raise forms.ValidationError(
                self.error_messages['wrong_password'])

    def save(self, *args, **kwargs):
        email = self.cleaned_data['email']
        if self.user.username == self.user.email:
            self.user.username = email
        self.user.email = email
        self.user.save()
        return self.user


class UpdatePasswordNoCurrentForm(GenesisForm, VerifyNewPasswordMixin):
    password = forms.CharField(
        min_length=8, max_length=100, widget=forms.PasswordInput,
        label="New password",
        help_text=PASSWORD_HELP_TEXT)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(UpdatePasswordNoCurrentForm, self).__init__(*args, **kwargs)

    def clean(self):
        self.verify_passwords()
        return super(UpdatePasswordNoCurrentForm, self).clean()

    def save(self, *args, **kwargs):
        set_password(self.user, self.cleaned_data['password'])


class UpdatePasswordForm(UpdatePasswordNoCurrentForm, VerifyPasswordMixin):
    confirm_password = forms.CharField(widget=forms.PasswordInput)


class ResetPasswordForm(GenesisForm, VerifyNewPasswordMixin):
    password = forms.CharField(
        min_length=8, max_length=100, widget=forms.PasswordInput,
        label="New password",
        help_text=PASSWORD_HELP_TEXT)
    confirm_password = forms.CharField(
        max_length=100, widget=forms.PasswordInput, label="Confirm password")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', getattr(self, 'user', None))
        super(ResetPasswordForm, self).__init__(*args, **kwargs)

    def clean(self):
        self.verify_passwords()
        return super(ResetPasswordForm, self).clean()

    def save(self):
        set_password(self.user, self.cleaned_data.get('password'))
        return self.user


class ResetPasswordEmailForm(GenesisForm):
    username = forms.CharField()

    def clean_username(self, *args, **kwargs):
        username = self.cleaned_data['username']
        try:
            user = User.objects.get(username=username)
            assert not user.is_admin()
        except (User.DoesNotExist, AssertionError):
            raise forms.ValidationError(
                "There was an error retrieving your information. Retry or "
                "please call us at {} for assistance.".format(
                    settings.GENESIS_SUPPORT_PHONE_NUMBER))
        return username

    def save(self, *args, **kwargs):
        user = User.objects.get(username=self.cleaned_data['username'])
        profile = user.get_profile()
        while True:
            hash_ = sha_constructor(str(random.random())).hexdigest()[8:16]
            try:
                if user.is_patient():
                    PatientProfile.objects.get(forgot_key=hash_)
                else:
                    ProfessionalProfile.objects.get(forgot_key=hash_)

            except profile.DoesNotExist:
                profile.forgot_key = hash_
                profile.forgot_key_updated = utcnow()
                profile.save()
                break

        ctx_dict = {
            'reset_link': 'http://%s/dashboard/public/#/accounts/reset/%s/' % (
                settings.SITE_URL, profile.forgot_key)}

        subject = render_to_string(
            'accounts/lost_password/email_subject.txt', ctx_dict)
        message = render_to_string(
            'accounts/lost_password/email_message.txt', ctx_dict)
        user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)

        return user


class ResetPasswordPhoneForm(ResetPasswordForm, AnswerSecurityQuestionMixin,
                             VerifyPhoneMixin):
    """
    The validation logic of this form is a bit complex. That is because the
    form depends on several hidden fields and some of the fields also depend
    on each other.

    The gist is that we first check if the provided username is valid and
    exists
    in the database. The username is taken from a hidden form field, so if
    there's a problem with it, we don't validate the other fields and we
    display an error message suggesting the restart of the password reset
    process.

    If the username is valid and it exists, we set it on the form and then we
    validate the phone and the match between the user, the security question
    and the answer.

    Finally, in the `clean` method, we remove error messages that we don't
    want the user to see and we display a more generic message.
    """
    username = forms.CharField(max_length=100, widget=forms.HiddenInput())
    question = forms.IntegerField(widget=forms.HiddenInput())
    security_question = forms.CharField(
        max_length=100, required=False, widget=SecurityQuestionWidget())
    answer = forms.CharField(max_length=100, widget=forms.TextInput)
    verify_phone = forms.CharField()

    def __init__(self, *args, **kwargs):
        super(ResetPasswordPhoneForm, self).__init__(*args, **kwargs)
        AnswerSecurityQuestionMixin.__init__(self, *args, **kwargs)

        # The user is set only on unbound forms, so that's why we also
        # do some adjustments to other fields
        user = getattr(self, 'user')
        if user is not None:
            # Setting the username on the hidden field
            self.fields['username'].initial = user.username

        # Putting the password fields last
        self.fields = OrderedDict(
            self.fields.items()[2:] +
            self.fields.items()[:2]
        )

    def clean(self):
        cleaned_data = super(ResetPasswordPhoneForm, self).clean()
        if 'username' not in cleaned_data:
            self._errors.pop('username')
            raise forms.ValidationError(
                "There was an error with the entered data. Please restart "
                "the process.")
        return cleaned_data

    def clean_username(self):
        try:
            # We store the user object on the form, because it's used in the
            # other validation methods and we don't want to query the database
            # every time
            self.user = User.objects.get(
                username=self.cleaned_data['username'])
            return self.user.username
        except User.DoesNotExist:
            raise forms.ValidationError("Error")

    def save(self, *args, **kwargs):
        set_password(self.user, self.cleaned_data['confirm_password'])


class ResetPasswordEmailFinishForm(ResetPasswordForm,
                                   AnswerSecurityQuestionMixin):
    """This form appears when an email user logs in for the first time after
    having their temporary password reset."""
    question = forms.IntegerField(widget=forms.HiddenInput())
    security_question = forms.CharField(
        max_length=100, required=False, widget=SecurityQuestionWidget())
    answer = forms.CharField(
        max_length=100, widget=forms.TextInput(attrs={'class': 'required'}))
    password = forms.CharField(
        min_length=8, max_length=100,
        widget=forms.PasswordInput(attrs={'class': 'required'}),
        label="New password",
        help_text=PASSWORD_HELP_TEXT)
    confirm_password = forms.CharField(
        max_length=100,
        widget=forms.PasswordInput(attrs={'class': 'required'}))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('requester')
        super(ResetPasswordEmailFinishForm, self).__init__(*args, **kwargs)
        AnswerSecurityQuestionMixin.__init__(self, *args, **kwargs)
        new_order = (
            'question', 'security_question', 'answer',
            'password', 'confirm_password')

        def sort_field(x):
            try:
                return new_order.index(x[0])
            except ValueError:
                return -1

        self.fields = OrderedDict(
            sorted(self.fields.items(), key=sort_field)
        )

    def clean(self):
        self.verify_passwords()
        return super(ResetPasswordEmailFinishForm, self).clean()

    def save(self, commit=True, **kwargs):
        super(ResetPasswordEmailFinishForm, self).save()
        profile = self.user.get_profile()
        profile.is_reset_password = False
        profile.save()


class SecurityQuestionsForm(GenesisForm, SecurityQuestionsMixin):
    security_question1 = forms.ChoiceField(
        choices=SECURITY_QUESTIONS, label="Security question 1")
    security_answer1 = forms.CharField(
        max_length=100, label="Security question answer 1")
    security_question2 = forms.ChoiceField(
        choices=SECURITY_QUESTIONS, label="Security question 2")
    security_answer2 = forms.CharField(
        max_length=100, label="Security question answer 2")
    security_question3 = forms.ChoiceField(
        choices=SECURITY_QUESTIONS, label="Security question 3")
    security_answer3 = forms.CharField(
        max_length=100, label="Security question answer 3")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(SecurityQuestionsForm, self).__init__(*args, **kwargs)

        profile = self.user.get_profile()
        self.fields['security_question1'].initial = profile.security_question1
        self.fields['security_question2'].initial = profile.security_question2
        self.fields['security_question3'].initial = profile.security_question3

    def save(self):
        profile = self.user.get_profile()
        for i in range(1, 4):
            q = 'security_question{0}'.format(i)
            a = 'security_answer{0}'.format(i)
            setattr(profile, q, self.cleaned_data[q])
            setattr(profile, a, self.cleaned_data[a])
        profile.save()

        return self.user


class PhonelessConfigureForm(SecurityQuestionsForm, VerifyNewPasswordMixin):
    password = forms.CharField(
        min_length=8, max_length=100, widget=forms.PasswordInput,
        label="New password",
        help_text=PASSWORD_HELP_TEXT)
    confirm_password = forms.CharField(
        max_length=100,
        widget=forms.PasswordInput,
        label="New password confirm")

    def __init__(self, *args, **kwargs):
        super(PhonelessConfigureForm, self).__init__(*args, **kwargs)
        new_order = [
            'password', 'confirm_password', 'security_question1',
            'security_answer1', 'security_question2', 'security_answer2',
            'security_question3', 'security_answer3', 'accept_terms',
            'verify_phone']
        self.fields = OrderedDict(
            sorted(self.fields.items(),
                   key=lambda x: new_order.index(x[0]))
        )

    def clean(self):
        self.verify_passwords()
        return super(PhonelessConfigureForm, self).clean()

    def save(self):
        super(PhonelessConfigureForm, self).save()
        set_password(self.user, self.cleaned_data['password'])
        self.user.save()
        profile = self.user.get_profile()
        profile.configured = True
        profile.save()
        return self.user


class ConfigureForm(PhonelessConfigureForm, VerifyPhoneMixin):
    verify_phone = forms.CharField(label="Phone number")

    def __init__(self, *args, **kwargs):
        super(ConfigureForm, self).__init__(*args, **kwargs)
        self.fields = OrderedDict(sorted(
            self.fields.items(),
            key=lambda x: x[0] != 'verify_phone'
        ))
        if len(self.user.email) != 0:
            del self.fields['verify_phone']


class AdminChangePasswordForm(GenesisForm, VerifyNewPasswordMixin):
    """Admin can set a user's password directly."""
    password = forms.CharField(
        min_length=8, max_length=100, widget=forms.PasswordInput,
        label="New password",
        help_text=PASSWORD_HELP_TEXT)
    confirm_password = forms.CharField(
        max_length=100,
        widget=forms.PasswordInput,
        label="New password confirm")
    form_name = forms.CharField(
        initial='change_password', widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('instance')
        super(AdminChangePasswordForm, self).__init__(*args, **kwargs)

    def clean(self):
        self.verify_passwords()
        return super(AdminChangePasswordForm, self).clean()

    def save(self, *args, **kwargs):
        profile = self.user.get_profile()
        if profile.configured:
            profile.is_reset_password = True
            profile.save()

        set_password(self.user, self.cleaned_data['password'])
        return self.user


class AdminChangeUsernameForm(GenesisModelForm):
    form_name = forms.CharField(
        initial='change_username', widget=forms.HiddenInput)

    class Meta:
        model = User
        fields = ('username', )

    def __init__(self, *args, **kwargs):
        super(AdminChangeUsernameForm, self).__init__(*args, **kwargs)
        self.update_email = self.instance.username == self.instance.email

    def save(self, *args, **kwargs):
        instance = super(AdminChangeUsernameForm, self).save(*args, **kwargs)
        # If user's email was an email before change, and new username is a
        # valid email, update email address.
        if self.update_email:
            try:
                validate_email(instance.username)
            except ValidationError:
                pass
            else:
                instance.email = instance.username
                instance.save()
        return instance


class AdminCheckSecurityQuestionForm(GenesisForm):
    """Verifies whether or not a given security question was answered
    correctly."""
    form_name = forms.CharField(
        initial='check_security_question',
        widget=forms.HiddenInput)
    question = forms.ChoiceField()
    answer = forms.CharField()

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('instance')
        super(AdminCheckSecurityQuestionForm, self).__init__(*args, **kwargs)
        self.fields['question'].choices = \
            self.user.get_profile().get_security_question_choices()

    def clean_answer(self):
        question = self.cleaned_data['question']
        answer = self.cleaned_data['answer']
        if self.user.get_profile().verify_security_question(question, answer):
            return answer
        raise forms.ValidationError('Incorrect answer.')

    def save(self):
        # We don't need to do anything.
        pass


class AdminSetDefaultPasswordForm(GenesisForm):
    new_password = forms.CharField(widget=forms.HiddenInput)
    form_name = forms.CharField(
        initial='set_default_password_form',
        widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('instance')
        password = kwargs.pop('password', None)
        super(AdminSetDefaultPasswordForm, self).__init__(*args, **kwargs)
        if password is not None:
            self.fields['new_password'].initial = password

    def save(self):
        set_password(self.user, self.cleaned_data['new_password'])


class PickStartEndMonthForm(GenesisForm):
    start_date = forms.DateField(
        help_text='Note: Report will always show data for the entire month '
                  'for any month included in the range.')
    end_date = forms.DateField()

    def __init__(self, *args, **kwargs):
        super(PickStartEndMonthForm, self).__init__(
            *args, **kwargs)
        default_end_date = now().date()
        default_start_date = default_end_date - relativedelta(months=3)
        self.fields['start_date'].initial = default_start_date
        self.fields['end_date'].initial = default_end_date

    def clean(self):
        data = self.cleaned_data
        if data['start_date'] >= data['end_date']:
            raise forms.ValidationError('End date must be after start date.')
        return data
