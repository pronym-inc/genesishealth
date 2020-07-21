from django import forms
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils.timezone import now

from localflavor.us.forms import USStateField, USStateSelect

from genesishealth.apps.accounts.models import ProfessionalProfile, Company
from genesishealth.apps.reports.models import TemporaryDownload
from genesishealth.apps.utils.forms import (
    GenesisForm, GenesisModelForm, PhoneField, SinglePhoneField, ZipField)
from genesishealth.apps.utils.forms import (
    PhoneNumberFormMixin, GenesisBatchForm)
from genesishealth.apps.utils.func import read_csv_file


class ProfessionalForm(PhoneNumberFormMixin, GenesisModelForm):
    CONTACT_FIELDS = (
        'salutation', 'middle_initial', 'address1', 'address2', 'city',
        'state', 'zip', 'fax')
    PROFILE_FIELDS = ('timezone_name', )

    salutation = forms.CharField(required=False)
    first_name = forms.CharField()
    middle_initial = forms.CharField(required=False)
    last_name = forms.CharField()
    email = forms.EmailField()
    confirm_email = forms.EmailField()
    address1 = forms.CharField(label='Address', required=False)
    address2 = forms.CharField(label='Address (cont.)', required=False)
    city = forms.CharField(required=False)
    state = USStateField(widget=USStateSelect, required=False)
    zip = ZipField(
        required=False, widget=forms.TextInput(attrs={'class': 'zip'}))
    phone = PhoneField(required=False)
    fax = forms.CharField(required=False)
    timezone_name = forms.ChoiceField(
        choices=ProfessionalProfile.ALLOWED_TIMEZONES, label="Timezone")

    class Meta:
        model = User
        fields = (
            'salutation', 'first_name', 'middle_initial', 'last_name',
            'email', 'confirm_email', 'address1', 'address2', 'city',
            'phone', 'fax', 'timezone_name')

    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester')
        self.initial_group = kwargs.pop('initial_group')
        super(ProfessionalForm, self).__init__(*args, **kwargs)

        if not self.is_new:
            for cf in ProfessionalForm.CONTACT_FIELDS:
                self.fields[cf].initial = getattr(
                    self.instance.professional_profile.contact, cf)
            for pf in ProfessionalForm.PROFILE_FIELDS:
                self.fields[pf].initial = getattr(
                    self.instance.professional_profile, pf)
            del self.fields['email']
            del self.fields['confirm_email']

    def get_phone_initialdata(self):
        return self.instance.professional_profile.contact.phone_numbers.all()

    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            if self.is_new:
                User.objects.get(Q(email=email) | Q(username=email))
            else:
                User.objects.exclude(pk=self.instance.pk).get(
                    Q(email=email) | Q(username=email))
        except User.DoesNotExist:
            return email
        else:
            raise forms.ValidationError(
                "The provided email address is already in use.  "
                "Please provide another.")

    def clean_confirm_email(self):
        email_address = self.cleaned_data.get('email')
        email_confirm = self.cleaned_data.get('confirm_email')
        if email_address != email_confirm:
            raise forms.ValidationError(
                'The provided emails did not match.  Please enter them again.')
        return email_confirm

    def save(self, commit=True, **kwargs):
        data = self.cleaned_data
        kwargs = {}
        kwargs.update(data)
        kwargs['parent_group'] = self.initial_group
        if data.get('email'):
            kwargs['username'] = data['email']
        if self.is_new:
            user = ProfessionalProfile.objects.create_user(**kwargs)
        else:
            user = self.instance
            user.professional_profile.update(save=True, **kwargs)

        self.save_phone(user.professional_profile.contact)

        return user


class ImportProfessionalForm(GenesisForm):
    csv = forms.FileField(label='Professionals CSV file')

    CSV_FIELD_NAMES = (
        'salutation', 'first_name', 'middle_initial', 'last_name', 'email',
        'address1', 'address2', 'city', 'state', 'zip', 'timezone_name',
        'phone', 'phone_type', 'fax')

    def __init__(self, *args, **kwargs):
        self.initial_group = kwargs.pop('initial_group')
        self.requester = kwargs.pop('requester')
        super(ImportProfessionalForm, self).__init__(*args, **kwargs)

    def clean_csv(self):
        self.forms = []
        emails = set()
        csv_data = read_csv_file(
            self.cleaned_data['csv'], self.CSV_FIELD_NAMES)
        for count, data in enumerate(csv_data, 1):
            data['phone_0_phone'] = data['phone']
            ptype = data['phone_type'].lower()
            if ptype == 'contact':
                data['phone_0_is_contact'] = True
            elif ptype == 'cell':
                data['phone_0_is_cell'] = True
            del data['phone'], data['phone_type']

            data['confirm_email'] = data['email']

            if data['email'] in emails:
                raise forms.ValidationError("Line {0} is invalid: {1}".format(
                    count,
                    "* email * Professional with this Email already exists "
                    "in CSV file."))
            emails.add(data['email'])
            p_form = ProfessionalForm(
                data, requester=self.requester,
                initial_group=self.initial_group)
            if not p_form.is_valid():
                raise forms.ValidationError("Line {0} is invalid: {1}".format(
                    count, p_form.errors.as_text().replace('\n', ' ')))
            self.forms.append(p_form)

    def save(self, *args, **kwargs):
        for form in self.forms:
            form.save()


class ProfessionalMyProfileForm(PhoneNumberFormMixin, GenesisModelForm):
    models_i_depend_on = [
        'professional_profile', 'professional_profile.contact']

    salutation = forms.CharField(required=False)
    first_name = forms.CharField()
    middle_initial = forms.CharField(required=False)
    last_name = forms.CharField()
    address1 = forms.CharField(required=False)
    address2 = forms.CharField(required=False)
    city = forms.CharField(required=False)
    state = USStateField(widget=USStateSelect, required=False)
    zip = ZipField(required=False)
    phone = PhoneField(required=False)
    fax = forms.CharField(required=False)

    class Meta:
        model = User
        fields = (
            'salutation', 'first_name', 'middle_initial', 'last_name',
            'phone', 'address1', 'address2', 'city', 'fax')

    def get_phone_initialdata(self):
        return self.instance.professional_profile.contact.phone_numbers.all()

    def save(self, *args, **kwargs):
        obj = super(ProfessionalMyProfileForm, self).save(*args, **kwargs)
        self.save_phone(obj.professional_profile.contact)


class BatchCaregiverAssignForm(GenesisBatchForm):
    def __init__(self, *args, **kwargs):
        self.professional = kwargs.pop('professional')
        super(BatchCaregiverAssignForm, self).__init__(*args, **kwargs)

    def save(self):
        for patient in self.batch:
            self.professional.professional_profile.add_patient(patient)


class BatchCaregiverUnassignForm(GenesisBatchForm):
    def __init__(self, *args, **kwargs):
        self.professional = kwargs.pop('professional')
        super(BatchCaregiverUnassignForm, self).__init__(*args, **kwargs)

    def save(self):
        for patient in self.batch:
            self.professional.professional_profile.remove_patient(patient)


class ProfessionalNoncompliantReportForm(GenesisForm):
    INTERVAL_HOUR = 'hour'
    INTERVAL_DAY = 'day'
    INTERVAL_CHOICES = (
        (INTERVAL_HOUR, 'Hour'),
        (INTERVAL_DAY, 'Day'),
    )

    report_period = forms.IntegerField(
        initial=1, label="Report Period",
        help_text=("Show patients that have not tested in the specified number"
                   " of days or hours.  Days are calculated by multiplying 24 "
                   "hours x days desired. Example: 2 Days = previous 48 hours "
                   "starting from the time the report is created."))
    period_interval = forms.ChoiceField(
        choices=INTERVAL_CHOICES)
    employer = forms.ModelChoiceField(
        queryset=None, required=False, label="Group",
        help_text="All groups will be included in report if blank.")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(ProfessionalNoncompliantReportForm, self).__init__(
            *args, **kwargs)
        self.fields['employer'].queryset = Company.objects.filter(
            id__in=self.user.professional_profile.get_patients().values(
                'patient_profile__company__id'))

    def clean(self):
        data = self.cleaned_data
        if data['period_interval'] == self.INTERVAL_DAY:
            data['report_period'] *= 24
        return data

    def get_download_id(self):
        if hasattr(self, 'download'):
            return self.download.id

    def save(self):
        content = self.user.professional_profile.generate_noncompliance_report(
            self.cleaned_data['report_period'],
            self.cleaned_data['employer']
        )
        cleaned_name = self.user.professional_profile.user.get_full_name()
        filename = "{}_noncompliant_{}.csv".format(
            cleaned_name,
            now().date()
        )
        self.download = TemporaryDownload.objects.create(
            for_user=self.user, content=content, content_type="text/csv",
            filename=filename
        )


class ProfessionalTargetRangeReportForm(GenesisForm):
    days_back = forms.IntegerField(
        initial=1, label="Report Period",
        help_text=(
            "Show patients that have tested out of safe zone range "
            "within the specified number of days."))
    employer = forms.ModelChoiceField(
        queryset=None, required=False, label="Group",
        help_text="All groups will be included in report if blank.")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(ProfessionalTargetRangeReportForm, self).__init__(
            *args, **kwargs)
        self.fields['employer'].queryset = Company.objects.filter(
            id__in=self.user.professional_profile.get_patients().values(
                'patient_profile__company__id'))

    def save(self):
        content = self.user.professional_profile.generate_target_range_report(
            self.cleaned_data['days_back'], self.cleaned_data['employer'])
        cleaned_name = self.user.professional_profile.user.get_full_name()
        if self.cleaned_data['employer'] is not None:
            cleaned_name += " ({})".format(self.cleaned_data['employer'].name)
        filename = "{}_target_range_{}.csv".format(
            cleaned_name,
            now().date()
        )
        self.download = TemporaryDownload.objects.create(
            for_user=self.user, content=content, content_type="text/csv",
            filename=filename
        )

    def get_download_id(self):
        if hasattr(self, 'download'):
            return self.download.id
