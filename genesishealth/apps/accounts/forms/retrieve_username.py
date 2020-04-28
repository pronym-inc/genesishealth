import random
from django import forms

from genesishealth.apps.gdrives.models import GDrive
from genesishealth.apps.utils.forms import GenesisForm, SecurityQuestionWidget
from genesishealth.apps.utils.forms import BirthdayWidget
from genesishealth.apps.accounts.models import PatientProfile, ProfessionalProfile, SECURITY_QUESTIONS


class UserInfoVerificationForm(GenesisForm):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    date_of_birth = forms.DateField(widget=BirthdayWidget(), required=False)
    phone_number = forms.CharField(required=False)
    meid = forms.CharField(max_length=100, help_text="<a href=\"#findMEID\">How to find your MEID</a>")

    error_messages = {
        'validation': 'There was an error verifying your information please retry or call Genesis at 888-263-0003',
    }

    def clean(self):
        cleaned_data = super(UserInfoVerificationForm, self).clean()

        try:
            user = GDrive.objects.get_assigned_devices().get(meid__iexact=cleaned_data['meid']).patient
            profile = user.get_profile()
        except (GDrive.DoesNotExist, PatientProfile.DoesNotExist, ProfessionalProfile.DoesNotExist):
            raise forms.ValidationError(self.error_messages['validation'])

        passing_tests = sum(map(bool, (
            profile.contact.first_name.lower() == cleaned_data['first_name'].lower(),
            profile.contact.last_name.lower() == cleaned_data['last_name'].lower(),
            profile.has_phone_number(cleaned_data['phone_number']),
            profile.date_of_birth == cleaned_data['date_of_birth'])))

        if passing_tests < 3:
            raise forms.ValidationError(self.error_messages['validation'])

        self.user = user
        return cleaned_data


class VerifySecurityQuestionForm(GenesisForm):
    question = forms.IntegerField(widget=forms.HiddenInput())
    security_question = forms.CharField(max_length=100, required=False, widget=SecurityQuestionWidget())
    answer = forms.CharField(max_length=100)

    error_messages = {
        'wrong_answer': 'The answer you gave is incorrect.',
    }

    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop('user').get_profile()
        super(VerifySecurityQuestionForm, self).__init__(*args, **kwargs)

        if self.is_bound:
            question_no = self.data['{0}-question'.format(self.prefix)]
        else:
            question_no = random.choice(range(1, 4))

        question_key = getattr(self.profile, 'security_question%s' % question_no)
        full_question = dict(SECURITY_QUESTIONS)[question_key]

        self.fields['security_question'].initial = full_question
        self.fields['question'].initial = question_no

        if self.is_bound:
            self.data = self.data.copy()
            self.data['{0}-security_question'.format(self.prefix)] = full_question

    def clean_answer(self):
        question_no = self.cleaned_data['question']
        question = getattr(self.profile, 'security_question%s' % question_no)
        if not self.profile.verify_security_question(question, self.cleaned_data['answer']):
            raise forms.ValidationError(self.error_messages['wrong_answer'])

    def save(self):
        pass
