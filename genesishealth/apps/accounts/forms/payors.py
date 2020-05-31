from django import forms

from localflavor.us.forms import USStateField, USStateSelect

from genesishealth.apps.accounts.models import Payor, Contact
from genesishealth.apps.utils.forms import (GenesisForm, GenesisModelForm, ZipField,
    PhoneField, PhoneNumberFormMixin)
from genesishealth.apps.utils.func import read_csv_file


class PayorForm(PhoneNumberFormMixin, GenesisModelForm):
    CONTACT_FIELDS = ('first_name', 'last_name', 'email', 'address1', 'address2', 'city',
        'state', 'zip')

    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField(required=False)
    phone = PhoneField(label='Phone', required=False)
    address1 = forms.CharField(label='Address', required=False)
    address2 = forms.CharField(label='Address (cont.)', required=False)
    city = forms.CharField(widget=forms.TextInput(attrs={'class': 'required'}))
    state = USStateField(widget=USStateSelect)
    zip = ZipField()

    class Meta:
        model = Payor
        fields = ('name', 'first_name', 'last_name', 'email', 'phone', 'address1', 'address2', 'city')

    def __init__(self, *args, **kwargs):
        if kwargs.get('initial_group'):
            self.initial_group = kwargs.pop('initial_group')
        elif kwargs.get('instance'):
            self.initial_group = kwargs['instance'].group
        else:
            self.initial_group = None
        super(PayorForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            for cf in PayorForm.CONTACT_FIELDS:
                self.fields[cf].initial = getattr(self.instance.contact, cf)

    def get_phone_initialdata(self):
        return self.instance.contact.phonenumber_set.all()

    def clean_name(self):
        name = self.cleaned_data.get('name')
        try:
            if self.instance.pk:
                self.initial_group.payors.exclude(pk=self.instance.pk).get(name=name)
            else:
                self.initial_group.payors.get(name=name)
        except Payor.DoesNotExist:
            return name
        else:
            raise forms.ValidationError('A payor with that name already exists.  Please choose another '
                'name.')

    def save(self, commit=True, **kwargs):
        payor = super(PayorForm, self).save(commit=False, **kwargs)
        payor.group = self.initial_group
        contact = payor.pk and payor.contact or Contact()
        for cf in PayorForm.CONTACT_FIELDS:
            setattr(contact, cf, self.cleaned_data.get(cf))
        contact.save()
        if not payor.pk:
            payor.contact = contact
        payor.save()
        self.save_phone(contact)
        return payor


class ImportPayorsForm(GenesisForm):
    csv = forms.FileField(label='Payors/TPA CSV file')

    CSV_FIELD_NAMES = ('name', 'first_name', 'last_name', 'email',
        'address1', 'address2', 'city', 'state', 'zip', 'phone', 'phone_type')

    def __init__(self, *args, **kwargs):
        self.initial_group = kwargs.pop('initial_group')
        super(ImportPayorsForm, self).__init__(*args, **kwargs)

    def clean_csv(self):
        names = set()
        self.forms = []
        csv_data = read_csv_file(self.cleaned_data['csv'], self.CSV_FIELD_NAMES)
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
                    count, "* name * Payor/TPA with this name already exists in CSV file."))
            names.add(data['name'])

            p_form = PayorForm(data, initial_group=self.initial_group)
            if not p_form.is_valid():
                raise forms.ValidationError("Line {0} is invalid: {1}".format(
                    count, p_form.errors.as_text().replace('\n', ' ')))
            self.forms.append(p_form)

    def save(self, *args, **kwargs):
        for form in self.forms:
            form.save()
