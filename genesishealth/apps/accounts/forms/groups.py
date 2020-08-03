from datetime import datetime, timedelta

from django import forms
from django.utils.timezone import now

from genesishealth.apps.accounts.models import GenesisGroup
from genesishealth.apps.reports.models import TemporaryDownload
from genesishealth.apps.utils.class_views.csv_report import CSVReportForm
from genesishealth.apps.utils.forms import GenesisForm, GenesisModelForm, PhoneField
from genesishealth.apps.utils.forms import PhoneNumberFormMixin
from genesishealth.apps.utils.func import read_csv_file
from genesishealth.apps.utils.us_states import US_STATES


class GroupForm(PhoneNumberFormMixin, GenesisModelForm):
    models_i_depend_on = ['contact']

    first_name = forms.CharField(required=False, label="Contact first name")
    last_name = forms.CharField(required=False, label="Contact last name")
    email = forms.EmailField(required=False, label="Contact email")
    phone = PhoneField(required=False, label="Contact primary phone")
    address1 = forms.CharField(required=False, label="Contact address")
    address2 = forms.CharField(required=False, label="Contact address (cont.)")
    city = forms.CharField(required=False, label="Contact city")
    state = forms.ChoiceField(choices=US_STATES, required=False)
    zip = forms.CharField(max_length=5, required=False, label="Contact zip")

    class Meta:
        model = GenesisGroup
        fields = (
            'name', 'group_type', 'first_name', 'last_name', 'email', 'phone',
            'address1', 'address2', 'city', 'is_no_pii')

    def get_phone_initialdata(self):
        return self.instance.contact.phone_numbers.all()

    def save(self, *args, **kwargs):
        obj = super(GroupForm, self).save(*args, **kwargs)
        self.save_phone(obj.contact)
        return obj


class ImportGroupsForm(GenesisForm):
    csv = forms.FileField(label='Groups CSV file')

    CSV_FIELD_NAMES = (
        'name', 'group_type', 'first_name', 'last_name', 'email',
        'phone', 'phone_type', 'address1', 'address2', 'city', 'state', 'zip')

    def clean_csv(self):
        self.forms = []
        names = set()
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

            if data['name'] in names:
                raise forms.ValidationError("Line {0} is invalid: {1}".format(
                    count,
                    "* name * Genesis group with this name already exists in "
                    "CSV file."))
            names.add(data['name'])

            g_form = GroupForm(data)
            if not g_form.is_valid():
                raise forms.ValidationError("Line {0} is invalid: {1}".format(
                    count, g_form.errors.as_text().replace('\n', ' ')))
            self.forms.append(g_form)

    def save(self, *args, **kwargs):
        for form in self.forms:
            form.save()


class ParticipationReportForm(GenesisForm):
    report_start = forms.DateField()
    report_end = forms.DateField()

    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop('group')
        self.user = kwargs.pop('user')
        super(ParticipationReportForm, self).__init__(*args, **kwargs)
        self.fields['report_start'].initial = (
            datetime.now() - timedelta(days=30)).date()
        self.fields['report_end'].initial = datetime.now().date()

    def save(self):
        content = self.group.generate_participation_report(
            self.cleaned_data['report_start'],
            self.cleaned_data['report_end'])
        cleaned_group_name = self.group.name.replace(' ', '_').lower()
        filename = "{}_participation_{}.csv".format(
            cleaned_group_name,
            now().date()
        )
        self.download = TemporaryDownload.objects.create(
            for_user=self.user, content=content, content_type="text/csv",
            filename=filename
        )

    def get_download_id(self):
        if hasattr(self, 'download'):
            return self.download.id


class ParticipationStatusReportForm(GenesisForm):
    report_start = forms.DateField()
    report_end = forms.DateField()

    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop('group')
        self.user = kwargs.pop('user')
        super(ParticipationStatusReportForm, self).__init__(*args, **kwargs)
        self.fields['report_start'].initial = (
            datetime.now() - timedelta(days=30)).date()
        self.fields['report_end'].initial = datetime.now().date()

    def save(self):
        content = self.get_report_content()
        cleaned_group_name = self.group.name.replace(' ', '_').lower()
        filename = "{0}_{1}_participation_status.csv".format(
            now().date().strftime("%Y%m%d"),
            cleaned_group_name
        )
        self.download = TemporaryDownload.objects.create(
            for_user=self.user, content=content, content_type="text/csv",
            filename=filename
        )

    def get_download_id(self):
        if hasattr(self, 'download'):
            return self.download.id

    def get_report_content(self):
        return self.group.generate_participation_status_report(
            self.cleaned_data['report_start'],
            self.cleaned_data['report_end'])


class InactiveParticipationStatusReportForm(ParticipationStatusReportForm):
    def get_report_content(self):
        return self.group.generate_inactive_participation_status_report(
            self.cleaned_data['report_start'],
            self.cleaned_data['report_end'])


class NoncompliantReportForm(GenesisForm):
    INTERVAL_HOUR = 'hour'
    INTERVAL_DAY = 'day'
    INTERVAL_CHOICES = (
        (INTERVAL_HOUR, 'Hour'),
        (INTERVAL_DAY, 'Day'),
    )

    report_period = forms.IntegerField(
        initial=1,
        label="Report period",
        help_text="Show patients that have not tested in the specified number "
                  "of days or hours.")
    period_interval = forms.ChoiceField(
        choices=INTERVAL_CHOICES,
        widget=forms.RadioSelect,
        initial=INTERVAL_HOUR)

    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop('group')
        self.user = kwargs.pop('user')
        super(NoncompliantReportForm, self).__init__(*args, **kwargs)

    def clean(self):
        data = self.cleaned_data
        if data['period_interval'] == self.INTERVAL_DAY:
            data['report_period'] *= 24
        return data

    def get_download_id(self):
        if hasattr(self, 'download'):
            return self.download.id

    def save(self):
        content = self.group.generate_noncompliance_report(
            self.cleaned_data['report_period'])
        cleaned_group_name = self.group.name.replace(' ', '_').lower()
        filename = "{}_noncompliant_{}.csv".format(
            cleaned_group_name,
            now().date()
        )
        self.download = TemporaryDownload.objects.create(
            for_user=self.user, content=content, content_type="text/csv",
            filename=filename
        )


class TargetRangeReportForm(GenesisForm):
    days_back = forms.IntegerField(
        initial=1,
        label="Report period",
        help_text="Show patients that have tested out of safe zone range "
                  "within the specified number of days.")

    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop('group')
        self.user = kwargs.pop('user')
        super(TargetRangeReportForm, self).__init__(*args, **kwargs)

    def save(self):
        content = self.group.generate_target_range_report(self.cleaned_data['days_back'])
        cleaned_group_name = self.group.name.replace(' ', '_').lower()
        filename = "{}_target_range_{}.csv".format(
            cleaned_group_name,
            now().date()
        )
        self.download = TemporaryDownload.objects.create(
            for_user=self.user, content=content, content_type="text/csv",
            filename=filename
        )

    def get_download_id(self):
        if hasattr(self, 'download'):
            return self.download.id


class ConfigurePatientExportForm(CSVReportForm):
    ACCOUNT_FILTER_ALL = 'all'
    ACCOUNT_FILTER_TODAY = 'today'
    ACCOUNT_FILTER_CUSTOM = 'custom'

    ACCOUNT_FILTER_CHOICES = (
        (ACCOUNT_FILTER_ALL, 'All'),
        (ACCOUNT_FILTER_TODAY, 'Created today'),
        (ACCOUNT_FILTER_CUSTOM, 'Created between...')
    )

    account_filter = forms.ChoiceField(
        choices=ACCOUNT_FILTER_CHOICES, widget=forms.RadioSelect,
        label="Accounts to export", initial=ACCOUNT_FILTER_ALL)
    report_start = forms.DateField(required=False)
    report_end = forms.DateField(required=False)

    class Media:
        js = ('pages/export_account/main.js',)

    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop('group')
        self.user = kwargs.pop('user')
        super(ConfigurePatientExportForm, self).__init__(*args, **kwargs)
        self.fields['report_start'].initial = (
            datetime.now() - timedelta(days=30)).date()
        self.fields['report_end'].initial = datetime.now().date()


class ConfigureExportAccountReportForm(ConfigurePatientExportForm):
    def __init__(self, *args, **kwargs):
        super(ConfigureExportAccountReportForm, self).__init__(*args, **kwargs)
        self.fields['company'].queryset = self.group.companies.all()

    company = forms.ModelChoiceField(queryset=None, label="Group")


class ConfigureAccountStatusReportForm(CSVReportForm):
    ACCOUNT_FILTER_ALL = 'all'
    ACCOUNT_FILTER_ACTIVE = 'active'
    ACCOUNT_FILTER_SUSPENDED = 'suspended'
    ACCOUNT_FILTER_TERMED = 'termed'

    ACCOUNT_FILTER_CHOICES = (
        (ACCOUNT_FILTER_ALL, 'All'),
        (ACCOUNT_FILTER_ACTIVE, 'Active Patients'),
        (ACCOUNT_FILTER_SUSPENDED, 'Suspended Patients'),
        (ACCOUNT_FILTER_TERMED, 'Termed Patients')
    )

    account_filter = forms.ChoiceField(
        choices=ACCOUNT_FILTER_CHOICES, widget=forms.RadioSelect,
        label="Accounts to export", initial=ACCOUNT_FILTER_ALL)
    company = forms.ModelChoiceField(queryset=None, label="Group")

    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop('group')
        self.user = kwargs.pop('user')
        super(ConfigureAccountStatusReportForm, self).__init__(*args, **kwargs)
        self.fields['company'].queryset = self.group.companies.all()


class ConfigureReadingDelayReportForm(CSVReportForm):
    start_date = forms.DateField()
    end_date = forms.DateField()
    companies = forms.ModelMultipleChoiceField(queryset=None)

    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop('group')
        self.user = kwargs.pop('user')
        super(ConfigureReadingDelayReportForm, self).__init__(*args, **kwargs)
        self.fields['companies'].queryset = self.group.companies.all()
