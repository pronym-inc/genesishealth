from django import forms
from django.contrib.auth.models import User

from localflavor.us.forms import USStateField, USStateSelect

from genesishealth.apps.accounts.models import Company, Contact, Payor, GenesisGroup
from genesishealth.apps.utils.class_views.csv_report import CSVReportForm
from genesishealth.apps.utils.forms import (
    GenesisForm, GenesisModelForm, PhoneField,
    ZipField, PhoneNumberFormMixin)
from genesishealth.apps.utils.func import read_csv_file


class CompanyForm(PhoneNumberFormMixin, GenesisModelForm):
    CONTACT_FIELDS = (
        'first_name', 'last_name', 'email', 'address1', 'address2', 'city',
        'state', 'zip',)

    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField()
    phone = PhoneField(label='Phone')
    address1 = forms.CharField(label='Address')
    address2 = forms.CharField(label='Address (cont.)', required=False)
    city = forms.CharField()
    state = USStateField(widget=USStateSelect)
    zip = ZipField()

    class Meta:
        model = Company
        fields = (
            'name', 'payor', 'first_name', 'last_name', 'email', 'phone', 'address1',
            'address2', 'city', 'group_identifier', 'billing_method',
            'refill_method', 'start_kit_size', 'minimum_refill_quantity', 'bin_id',
            'pcn_id', 'glucose_control_refill_frequency', 'lancing_refill_frequency',
            'default_pharmacy', 'api_partner', 'nursing_group')

    def __init__(self, *args, **kwargs):
        self.initial_group = kwargs.pop('initial_group')
        super(CompanyForm, self).__init__(*args, **kwargs)
        self.fields['payor'].queryset = self.initial_group.payors.all()
        if self.instance.pk:
            for cf in CompanyForm.CONTACT_FIELDS:
                self.fields[cf].initial = getattr(self.instance.contact, cf)

    def get_phone_initialdata(self):
        return self.instance.contact.phone_numbers.all()

    def clean_name(self):
        name = self.cleaned_data.get('name')
        try:
            if self.instance.pk:
                self.initial_group.companies.exclude(pk=self.instance.pk).get(
                    name=name)
            else:
                self.initial_group.companies.get(name=name)
        except Company.DoesNotExist:
            return name
        else:
            raise forms.ValidationError(
                'A company with that name already exists.  Please choose '
                'another name.')

    def save(self, commit=True, **kwargs):
        company = super(CompanyForm, self).save(commit=False, **kwargs)

        company.group = self.initial_group
        contact = company.pk and company.contact or Contact()
        for cf in CompanyForm.CONTACT_FIELDS:
            setattr(contact, cf, self.cleaned_data.get(cf))
        contact.save()
        if not company.pk:
            company.contact = contact
        company.save()
        self.save_phone(contact)
        return company


class ImportCompaniesForm(GenesisForm):
    csv = forms.FileField(label='Companies CSV file')

    CSV_FIELD_NAMES = (
        'name', 'first_name', 'last_name', 'email',
        'address1', 'address2', 'city', 'state', 'zip', 'phone',
        'phone_type', 'payor')

    def __init__(self, *args, **kwargs):
        self.initial_group = kwargs.pop('initial_group')
        super(ImportCompaniesForm, self).__init__(*args, **kwargs)

    def clean_csv(self):
        names = set()
        self.forms = []
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

            payor_name = data['payor']
            try:
                data['payor'] = Payor.objects.get(
                    name=payor_name, group=self.initial_group).id
            except Payor.DoesNotExist:
                msg = '* payor * A payor with the name {0} does not exist ' \
                      'in this Group.'.format(payor_name)
                raise forms.ValidationError("Line {0} is invalid: {1}".format(
                    count, msg))

            if data['name'] in names:
                raise forms.ValidationError(
                    "Line {0} is invalid: {1}".format(
                        count,
                        "* name * Company with this name already exists in "
                        "CSV file."))
            names.add(data['name'])

            p_form = CompanyForm(data, initial_group=self.initial_group)
            if not p_form.is_valid():
                raise forms.ValidationError("Line {0} is invalid: {1}".format(
                    count, p_form.errors.as_text().replace('\n', ' ')))
            self.forms.append(p_form)

    def save(self, *args, **kwargs):
        for form in self.forms:
            form.save()


class ConfigureGlucoseAverageReportForm(CSVReportForm):
    start_date = forms.DateField()
    end_date = forms.DateField()
    company = forms.ModelChoiceField(queryset=None, required=False)

    _group: GenesisGroup
    _user: User

    def __init__(self, *args, **kwargs):
        self._group = kwargs.pop('group')
        self._user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['company'].queryset = self._group.companies.all()
