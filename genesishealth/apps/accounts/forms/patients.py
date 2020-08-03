import csv
import io

from datetime import datetime, timedelta

from django import forms
from django.contrib.auth.models import User
from django.db.models import Q
from django.forms.widgets import RadioSelect
from django.utils.timezone import get_default_timezone, localtime, now

from celery.task import chord

from genesishealth.apps.accounts.models import (
    PatientProfile, Note, Company)
from genesishealth.apps.accounts.models.profile_patient import (
    PatientCommunication, PatientCommunicationNote)
from genesishealth.apps.accounts.tasks import (
    process_patient_form_data, process_patient_form_data_row)
from genesishealth.apps.utils.forms import (
    GenesisForm, GenesisBatchForm, GenesisModelForm,
    PhoneField, ZipField, BirthdayWidget, PhoneNumberFormMixin)
from genesishealth.apps.api.models import APIPartner
from genesishealth.apps.api.tasks import migrate_readings
from genesishealth.apps.dropdowns.models import (
    CommunicationResolution, DeactivationReason)
from genesishealth.apps.nursing.models import NursingGroup
from genesishealth.apps.pharmacy.models import PharmacyPartner
from genesishealth.apps.products.models import ProductType
from genesishealth.apps.reports.models import TemporaryDownload
from genesishealth.apps.utils.func import read_csv_file, expand_birthday_year
from genesishealth.apps.utils.us_states import US_STATES
from genesishealth.apps.utils.widgets import (
    AdditionalModelMultipleChoiceWidget)


class PatientForm(PhoneNumberFormMixin, GenesisModelForm):
    CONTACT_FIELDS = ('salutation', 'middle_initial', 'address1', 'address2',
                      'city', 'state', 'zip')
    PROFILE_FIELDS = (
        'company', 'preferred_contact_method', 'gender',
        'date_of_birth', 'insurance_identifier',
        'bin_number', 'pcn_number', 'billing_method', 'refill_method',
        'rx_partner', 'epc_member_identifier', 'nursing_group')

    account_number = forms.IntegerField(required=False)
    epc_member_identifier = forms.CharField(
        required=False, label="EPC Member ID")
    insurance_identifier = forms.CharField(required=False)
    salutation = forms.CharField(required=False)
    first_name = forms.CharField(required=False)
    middle_initial = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    gender = forms.ChoiceField(
        choices=PatientProfile.GENDER_CHOICES, required=False)
    date_of_birth = forms.DateField(widget=BirthdayWidget())
    email = forms.EmailField(label="Email", required=False)
    email_confirm = forms.EmailField(required=False)
    address1 = forms.CharField(label='Address', required=False)
    address2 = forms.CharField(required=False, label='Address (Line 2)')
    city = forms.CharField(required=False)
    state = forms.ChoiceField(choices=US_STATES, required=False)
    zip = ZipField(required=False)
    phone = PhoneField(required=False, label="Primary phone")
    preferred_contact_method = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=PatientProfile.PREFERRED_CONTACT_METHOD_CHOICES,
        initial="email")
    company = forms.ModelChoiceField(queryset=None, required=False)
    bin_number = forms.CharField(required=False, label="BIN")
    pcn_number = forms.CharField(required=False, label="PCN")
    billing_method = forms.ChoiceField(
        choices=PatientProfile.BILLING_METHOD_CHOICES,
        initial=PatientProfile.BILLING_METHOD_MEDICAL,
        required=False)
    refill_method = forms.ChoiceField(
        choices=PatientProfile.REFILL_METHOD_CHOICES,
        initial=PatientProfile.REFILL_METHOD_UTILIZATION,
        required=False)
    rx_partner = forms.ModelChoiceField(
        queryset=PharmacyPartner.objects.all(), required=False)
    nursing_group = forms.ModelChoiceField(
        queryset=NursingGroup.objects.all(), required=False)

    class Meta:
        model = User
        fields = (
            'account_number', 'epc_member_identifier', 'insurance_identifier',
            'salutation', 'first_name', 'middle_initial', 'last_name',
            'gender', 'date_of_birth', 'email', 'email_confirm', 'address1',
            'address2', 'city', 'phone',
            'preferred_contact_method', 'company',
            'bin_number', 'pcn_number', 'billing_method', 'refill_method',
            'rx_partner', 'nursing_group')

    def __init__(self, *args, **kwargs):
        self.initial_group = kwargs.pop('initial_group')
        self.supplied_username = kwargs.pop('supplied_username', None)
        super(PatientForm, self).__init__(*args, **kwargs)
        self.is_new = self.instance.pk is None
        if not self.is_new:
            self.fields['account_number'].widget.attrs['readonly'] = True
            self.fields['account_number'].initial = self.instance.pk
            self.fields['epc_member_identifier'].widget.attrs['readonly'] = \
                True
            self.fields['epc_member_identifier'].initial = \
                self.instance.patient_profile.epc_member_identifier

        if self.initial_group:
            self.fields['company'].queryset = \
                self.initial_group.companies.all()
        else:
            self.fields['company'].queryset = Company.objects.none()

        if not self.is_new:
            for cf in PatientForm.CONTACT_FIELDS:
                self.fields[cf].initial = getattr(self.instance.patient_profile.contact, cf)
            for pf in PatientForm.PROFILE_FIELDS:
                self.fields[pf].initial = getattr(self.instance.patient_profile, pf)
            del self.fields['email']
            del self.fields['email_confirm']

    def get_phone_initialdata(self):
        return self.instance.patient_profile.contact.phone_numbers.all()

    def clean(self):
        cleaned_data = super(PatientForm, self).clean()
        for field in ('epc_member_identifier', 'insurance_identifier'):
            if field in cleaned_data and cleaned_data[field] == '':
                cleaned_data[field] = None
        if self.is_new:
            if cleaned_data.get('preferred_contact_method') == 'email':
                if not cleaned_data.get('email'):
                    raise forms.ValidationError(
                        'If you specify email as the preferred method of '
                        'contact, you must provide an email.')
            elif cleaned_data.get('preferred_contact_method') == 'phone':
                if not len(list(filter(lambda pn: len(pn.phone) != 0,
                                  cleaned_data.get('phone')))):
                    raise forms.ValidationError(
                        'If you choose phone as your primary method of '
                        'contact, you must provide a phone number.')
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            return email
        if len(email) == 0:
            return ''
        try:
            users = User.objects.all()
            if not self.is_new:
                users = users.exclude(pk=self.instance.pk)
            users.get(Q(email=email) | Q(username=email))
        except User.DoesNotExist:
            return email
        else:
            raise forms.ValidationError(
                'The email you provided is already in use.  '
                'Please provide another.')

    def clean_email_confirm(self):
        email_address = self.cleaned_data.get('email')
        email_confirm = self.cleaned_data.get('email_confirm')
        if email_address and email_address != email_confirm:
            raise forms.ValidationError(
                'The emails you provided did not match.  '
                'Please enter them again.')
        return email_address

    def clean_insurance_identifier(self):
        ins_id = self.cleaned_data['insurance_identifier']
        if ins_id is not None and ins_id != '':
            qs = PatientProfile.objects.filter(insurance_identifier=ins_id)
            if not self.is_new:
                qs = qs.exclude(pk=self.instance.patient_profile.pk)
            if qs.count() > 0:
                raise forms.ValidationError(
                    "A user with this insurance ID already exists in "
                    "the system.")
        return ins_id

    def save(self, *args, **kwargs):
        data = self.cleaned_data.copy()
        data['group'] = self.initial_group
        if self.is_new:
            if self.supplied_username is not None:
                data['username'] = self.supplied_username
            patient = PatientProfile.myghr_patients.create_user(**data)
        else:
            patient = self.instance
            patient.patient_profile.update(save=True, **data)

        # Save phone numbers.
        self.save_phone(patient.patient_profile.contact)
        self.initial_group.add_patient(patient)

        return patient


class PatientWizardForm(PatientForm):
    CONTACT_FIELDS = (
        'salutation', 'middle_initial', 'address1', 'address2', 'city',
        'state', 'zip',)
    PROFILE_FIELDS = (
        'company', 'preferred_contact_method', 'gender', 'date_of_birth',
        'security_question1', 'security_question2', 'security_question3',
        'security_answer1', 'security_answer2', 'security_answer3',
        'insurance_identifier', 'pcn_number', 'bin_number', 'billing_method',
        'rx_partner', 'epc_member_identifier')

    insurance_identifier = forms.CharField()
    salutation = forms.CharField(required=False)
    first_name = forms.CharField()
    middle_initial = forms.CharField(required=False)
    last_name = forms.CharField()
    gender = forms.ChoiceField(choices=PatientProfile.GENDER_CHOICES)
    date_of_birth = forms.DateField(widget=BirthdayWidget())
    email = forms.EmailField(label="Email", required=False)
    email_confirm = forms.EmailField(required=False)
    address1 = forms.CharField(label='Address')
    address2 = forms.CharField(required=False, label='Address (Line 2)')
    city = forms.CharField()
    state = forms.ChoiceField(choices=US_STATES, required=False)
    zip = ZipField()
    phone = PhoneField(required=False, label="Primary phone")
    preferred_contact_method = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=PatientProfile.PREFERRED_CONTACT_METHOD_CHOICES,
        initial="email")
    company = forms.ModelChoiceField(queryset=None, required=False)
    bin_number = forms.CharField(required=False, label="BIN")
    pcn_number = forms.CharField(required=False, label="PCN")
    billing_method = forms.ChoiceField(
        choices=PatientProfile.BILLING_METHOD_CHOICES,
        initial=PatientProfile.BILLING_METHOD_MEDICAL)
    refill_method = forms.ChoiceField(
        choices=PatientProfile.REFILL_METHOD_CHOICES,
        initial=PatientProfile.REFILL_METHOD_UTILIZATION)
    rx_partner = forms.ModelChoiceField(
        queryset=PharmacyPartner.objects.all(), required=False)

    class Meta:
        model = User
        fields = (
            'account_number', 'insurance_identifier', 'salutation',
            'first_name', 'middle_initial', 'last_name', 'gender',
            'date_of_birth', 'email', 'email_confirm', 'address1', 'address2',
            'city', 'phone', 'preferred_contact_method',
            'company', 'bin_number', 'pcn_number', 'billing_method',
            'refill_method', 'rx_partner')

    def clean(self):
        qs = PatientProfile.objects.filter(
            date_of_birth=self.cleaned_data['date_of_birth'],
            user__last_name=self.cleaned_data['last_name'])
        if qs.count() > 0:
            raise forms.ValidationError(
                "Patient with this DOB / Last name already exists.")


class ImportPatientLineForm(PatientForm):
    def __init__(self, *args, **kwargs):
        super(ImportPatientLineForm, self).__init__(*args, **kwargs)
        self.fields['date_of_birth'].widget = forms.widgets.TextInput()


class ImportPatientForm(GenesisForm):
    company = forms.ModelChoiceField(queryset=None, required=False)
    csv = forms.FileField(label='Patients CSV file')

    CSV_FIELD_NAMES = (
        'salutation', 'first_name', 'middle_initial', 'last_name', 'gender',
        'date_of_birth', 'email', 'address1', 'address2', 'city', 'state',
        'zip', 'timezone_name', 'phone', 'phone_type',
        'preferred_contact_method', 'insurance_identifier', 'bin_number',
        'pcn_number', 'billing_method', 'refill_method', 'rx_partner',
        'username')

    def __init__(self, *args, **kwargs):
        self.initial_group = kwargs.pop('initial_group')
        self.user = kwargs.pop('user')
        super(ImportPatientForm, self).__init__(*args, **kwargs)
        self.fields['company'].queryset = self.initial_group.companies.all()

    def clean(self):
        self.forms = []
        self.datas = []
        csv_data = read_csv_file(
            self.cleaned_data['csv'], self.CSV_FIELD_NAMES)
        patients = User.objects.filter(patient_profile__isnull=False)
        taken_usernames = list(map(
            lambda x: x['username'], patients.values('username')))
        for count, data in enumerate(csv_data, 1):
            if not data['first_name']:
                continue
            data['phone_0_phone'] = data['phone']
            ptype = data['phone_type'].lower()
            if ptype == 'contact':
                data['phone_0_is_contact'] = True
            elif ptype == 'cell':
                data['phone_0_is_cell'] = True
            del data['phone'], data['phone_type']
            data['email_confirm'] = data['email']

            try:
                month, day, year = data['date_of_birth'].split('/')
            except ValueError:
                pass
            else:
                if len(year) == 2:
                    full_year = expand_birthday_year(year)
                    data['date_of_birth'] = '/'.join(
                        [month, day, str(full_year)])
            raw_data = data.copy()
            line_form_kwargs = {'initial_group': self.initial_group}
            username = data.pop('username', None)
            if username:
                try:
                    user = patients.get(username=username)
                except User.DoesNotExist:
                    raise forms.ValidationError(
                        "Invalid username: {}".format(username))
                line_form_kwargs['instance'] = user
            else:
                new_username = PatientProfile.generate_username(
                    data['email'],
                    data['first_name'],
                    data['last_name'],
                    also_skip=taken_usernames,
                    skip_db_check=True)
                taken_usernames.append(new_username)
                line_form_kwargs['supplied_username'] = new_username
                raw_data['username'] = new_username
            data['company'] = self.cleaned_data['company'].id
            p_form = ImportPatientLineForm(data, **line_form_kwargs)
            if not p_form.is_valid():
                raise forms.ValidationError("Line {0} is invalid: {1}".format(
                    count, p_form.errors.as_text().replace('\n', ' ')))
            self.datas.append(raw_data)
            self.forms.append(p_form)
            return self.cleaned_data

    def save(self, *args, **kwargs):
        # If we have too many, do this asynchronously.
        if len(self.datas) > 200:
            task_args = [self.initial_group.id]
            if self.cleaned_data['company']:
                task_args.append(self.cleaned_data['company'].id)
            else:
                task_args.append(None)
            chord(
                process_patient_form_data_row.subtask(
                    [data] + task_args) for data in self.datas
            )(process_patient_form_data.subtask([self.user.id]))
        else:
            patient_ids = []
            for form in self.forms:
                patient = form.save(commit=False)
                patient.patient_profile.company = self.cleaned_data['company']
                patient.patient_profile.save()
                patient_ids.append(patient.pk)
            patients = User.objects.filter(id__in=patient_ids)
            content = PatientProfile.generate_csv2(patients)
            self.download = TemporaryDownload.objects.create(
                for_user=self.user, content=content, content_type='text/csv',
                filename='imported_patients.csv'
            )

    def get_download_id(self):
        if hasattr(self, 'download'):
            return self.download.pk


class UpdateNotesForm(GenesisModelForm):
    class Meta:
        fields = ('content',)
        model = Note

    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester')
        self.patient = kwargs.pop('patient')
        super(UpdateNotesForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        note = super(UpdateNotesForm, self).save(commit=False, *args, **kwargs)
        note.patient = self.patient
        note.author = self.requester
        note.save()
        return note


class PatientMyProfileForm(PhoneNumberFormMixin, GenesisForm):
    PROFILE_FIELDS = ('gender', 'date_of_birth')
    CONTACT_FIELDS = (
        'salutation', 'middle_initial', 'address1', 'address2', 'city',
        'state', 'zip')
    USER_FIELDS = ('first_name', 'last_name')

    """This form is the one used by the patient when updating their own
    profile."""
    salutation = forms.CharField(required=False)
    first_name = forms.CharField()
    middle_initial = forms.CharField(required=False)
    last_name = forms.CharField()
    gender = forms.ChoiceField(choices=PatientProfile.GENDER_CHOICES)
    date_of_birth = forms.DateField(widget=BirthdayWidget())
    address1 = forms.CharField(label='Address')
    address2 = forms.CharField(required=False, label='Address (Line 2)')
    city = forms.CharField()
    state = forms.ChoiceField(choices=US_STATES, required=False)
    zip = ZipField()
    phone = PhoneField(required=False)

    def __init__(self, *args, **kwargs):
        self.patient = kwargs['patient']
        del kwargs['patient']
        super(PatientMyProfileForm, self).__init__(*args, **kwargs)
        for i in (
                (self.patient, PatientMyProfileForm.USER_FIELDS),
                (self.patient.patient_profile.contact,
                    PatientMyProfileForm.CONTACT_FIELDS),
                (self.patient.patient_profile,
                    PatientMyProfileForm.PROFILE_FIELDS)):
            for j in i[1]:
                self.fields[j].initial = getattr(i[0], j)

    def get_phone_initialdata(self):
        return self.patient.patient_profile.contact.phone_numbers.all()

    def save(self):
        for i in (
                (self.patient, PatientMyProfileForm.USER_FIELDS),
                (self.patient.patient_profile.contact,
                    PatientMyProfileForm.CONTACT_FIELDS),
                (self.patient.patient_profile,
                    PatientMyProfileForm.PROFILE_FIELDS)):
            for j in i[1]:
                setattr(i[0], j, self.cleaned_data.get(j))
            i[0].save()

        self.save_phone(self.patient.patient_profile.contact)

        return self.patient


class BatchAssignPatientForm(GenesisBatchForm):
    professional = forms.ModelChoiceField(queryset=None)

    def __init__(self, *args, **kwargs):
        professionals = kwargs.pop('professionals')
        super(BatchAssignPatientForm, self).__init__(*args, **kwargs)
        self.fields['professional'].queryset = professionals

    def save(self):
        for patient in self.batch:
            self.cleaned_data.get('professional')\
                .professional_profile\
                .add_patient(patient)


class BatchUnassignPatientForm(GenesisBatchForm):
    def save(self):
        for patient in self.batch:
            patient.patient_profile.remove_caregiver()


class BatchAddToWatchListForm(GenesisBatchForm):
    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester')
        super(BatchAddToWatchListForm, self).__init__(*args, **kwargs)

    def save(self):
        for patient in self.batch:
            self.requester.professional_profile.add_to_watch_list(patient)


class BatchRemoveFromWatchListForm(GenesisBatchForm):
    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester')
        super(BatchRemoveFromWatchListForm, self).__init__(*args, **kwargs)

    def save(self):
        for patient in self.batch:
            self.requester.professional_profile.remove_from_watch_list(patient)


class BatchAssignToAPIPartnerForm(GenesisBatchForm):
    partner = forms.ModelChoiceField(queryset=APIPartner.objects.all())
    clear_others = forms.BooleanField(initial=False, required=False)

    def save(self):
        partner = self.cleaned_data['partner']
        for patient in self.batch:
            partner.add_patient(
                patient, clear_others=self.cleaned_data['clear_others'])


class BatchUnassignFromAPIPartnerForm(GenesisBatchForm):
    partner = forms.ModelChoiceField(queryset=APIPartner.objects.all())

    def save(self):
        partner = self.cleaned_data['partner']
        for patient in self.batch:
            partner.remove_patient(patient)


class BatchMigrateForm(GenesisBatchForm):
    def save(self):
        batch_ids = map(lambda x: x['pk'], self.batch.values('pk'))
        migrate_readings.delay(batch_ids)


class BatchRecoverReadingsForm(GenesisBatchForm):
    starting_from = forms.DateField(
        help_text="Enter a date in the format MM/DD/YY")

    def save(self):
        for patient in self.batch:
            device = patient.patient_profile.get_device()
            if device is not None:
                device.recover_readings(self.cleaned_data['starting_from'])


class ActivateForm(GenesisForm):
    effective_date = forms.DateField()
    notification_method = forms.CharField()

    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester')
        self.patient = kwargs.pop('patient')
        super(ActivateForm, self).__init__(*args, **kwargs)
        self.fields['effective_date'].initial = localtime(now()).date()

    def save(self):
        self.patient.patient_profile.change_account_status(
            requested_by=self.requester,
            effective_date=self.cleaned_data['effective_date'],
            notification_method=self.cleaned_data['notification_method'],
            new_status=PatientProfile.ACCOUNT_STATUS_ACTIVE)


DEAC_STATUS_CHOICES = filter(
    lambda x: x[0] != PatientProfile.ACCOUNT_STATUS_ACTIVE,
    PatientProfile.ACCOUNT_STATUS_CHOICES
)


class DeactivateForm(GenesisForm):
    reason = forms.ModelChoiceField(
        queryset=DeactivationReason.objects.all())
    new_status = forms.ChoiceField(choices=DEAC_STATUS_CHOICES)
    effective_date = forms.DateField()
    notification_method = forms.CharField()

    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester')
        self.patient = kwargs.pop('patient')
        super(DeactivateForm, self).__init__(*args, **kwargs)
        self.fields['effective_date'].initial = localtime(now()).date()

    def save(self):
        self.patient.patient_profile.change_account_status(
            requested_by=self.requester,
            reason=self.cleaned_data['reason'],
            effective_date=self.cleaned_data['effective_date'],
            notification_method=self.cleaned_data['notification_method'],
            new_status=self.cleaned_data['new_status'])


class BatchActivateForm(GenesisBatchForm):
    effective_date = forms.DateField()
    notification_method = forms.CharField()

    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester')
        super(BatchActivateForm, self).__init__(*args, **kwargs)
        self.fields['effective_date'].initial = localtime(now()).date()

    def save(self):
        effective_date = self.cleaned_data['effective_date']
        notification_method = self.cleaned_data['notification_method']
        for patient in self.batch:
            patient.patient_profile.change_account_status(
                requested_by=self.requester,
                effective_date=effective_date,
                notification_method=notification_method,
                new_status=PatientProfile.ACCOUNT_STATUS_ACTIVE)


class BatchDeactivateForm(GenesisBatchForm):
    reason = forms.ModelChoiceField(
        queryset=DeactivationReason.objects.all())
    new_status = forms.ChoiceField(choices=DEAC_STATUS_CHOICES)
    effective_date = forms.DateField()
    notification_method = forms.CharField()

    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester')
        super(BatchDeactivateForm, self).__init__(*args, **kwargs)
        self.fields['effective_date'].initial = localtime(now()).date()

    def save(self):
        reason = self.cleaned_data['reason']
        effective_date = self.cleaned_data['effective_date']
        notification_method = self.cleaned_data['notification_method']
        for patient in self.batch:
            patient.patient_profile.change_account_status(
                requested_by=self.requester,
                reason=reason,
                effective_date=effective_date,
                notification_method=notification_method,
                new_status=self.cleaned_data['new_status'])


class PatientCommunicationForm(GenesisModelForm):
    class Meta:
        model = PatientCommunication
        fields = (
            'subject', 'category', 'subcategory', 'description'
        )

    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester', None)
        self.patient = kwargs.pop('patient', None)
        readonly = kwargs.pop('readonly', False)
        super(PatientCommunicationForm, self).__init__(*args, **kwargs)
        if readonly:
            for field_name, field in self.fields.items():
                field.disabled = True

    def save(self, commit=True, **kwargs):
        instance = super(PatientCommunicationForm, self).save(commit=False, **kwargs)
        if instance.pk is None:
            instance.added_by = self.requester
        instance.touch(self.requester)
        instance.patient = self.patient
        if commit:
            instance.save()
        return instance


class PatientCommunicationNoteForm(GenesisModelForm):
    replacements = forms.ModelMultipleChoiceField(
        queryset=ProductType.objects.all(),
        widget=AdditionalModelMultipleChoiceWidget,
        required=False)
    quality_improvement_category = forms.ChoiceField(
        choices=PatientCommunicationNote.QI_CATEGORY_CHOICES,
        widget=RadioSelect)
    resolution = forms.ModelChoiceField(
        queryset=CommunicationResolution.objects.all(),
        required=False)

    class Meta:
        model = PatientCommunicationNote
        fields = ('content', 'quality_improvement_category',
                  'has_replacements', 'is_rma', 'replacements',
                  'change_status_to', 'resolution')

    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester', None)
        self.existing_communication = kwargs.pop('communication', None)
        readonly = kwargs.pop('readonly', False)
        super(PatientCommunicationNoteForm, self).__init__(*args, **kwargs)
        self.fields['change_status_to'].label = 'Status'
        if readonly:
            for field_name, field in self.fields.items():
                field.disabled = True

    def clean(self):
        data = self.cleaned_data
        if data['change_status_to'].is_closed:
            if data['resolution'] is None:
                raise forms.ValidationError(
                    'You must choose a resolution if closing this '
                    'communication.')

    def save(self, communication=None, commit=True):
        instance = super(PatientCommunicationNoteForm, self).save(commit=False)
        instance.added_by = self.requester
        if communication is None:
            communication = self.existing_communication
        instance.communication = communication
        instance.communication.status = instance.change_status_to
        if instance.change_status_to.is_closed:
            if instance.resolution:
                instance.communication.resolution = instance.resolution
            instance.communication.datetime_closed = now()
        instance.communication.touch(self.requester)
        instance.communication.save()
        if commit:
            instance.save()
        if self.cleaned_data['has_replacements']:
            for replacement in self.cleaned_data['replacements']:
                instance.replacements.add(replacement)
        return instance


class CallLogReportForm(GenesisForm):
    start_date = forms.DateField()
    end_date = forms.DateField()

    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester', None)
        super(CallLogReportForm, self).__init__(*args, **kwargs)

    def get_download_id(self):
        if hasattr(self, 'download'):
            return self.download.pk

    def save(self):
        tz = get_default_timezone()
        start_date = self.cleaned_data['start_date']
        end_date = self.cleaned_data['end_date']
        start = (tz.localize(datetime(
            start_date.year, start_date.month, start_date.day)) +
            timedelta(days=1) - timedelta(microseconds=1))
        end = (tz.localize(datetime(
            end_date.year, end_date.month, end_date.day)) +
            timedelta(days=1) - timedelta(microseconds=1))
        qs = PatientCommunicationNote.objects.filter(
            datetime_added__range=(start, end))
        output_buffer = io.StringIO()
        writer = csv.writer(output_buffer)
        headers = [
            'Insurance ID', 'Caller Name', 'Call Date', 'GHT Agent Name',
            'Call Subject', 'Call Category', 'Call Subcategory',
            'Call Description', 'Note Date/Time', 'Agent Notes', 'QI Category',
            'Replaced Products', 'Warranty Authorization',
            'Note Changed Status To', 'Current Communication Status',
            'Employer', 'Resolution']
        writer.writerow(headers)
        for row in qs:
            output = [
                row.communication.patient.patient_profile.insurance_identifier,
                row.communication.patient.get_full_name(),
                row.communication.datetime_added,
                row.added_by.get_full_name() if row.added_by else '',
                row.communication.subject,
                row.communication.category.name,
                row.communication.subcategory.name,
                row.communication.description,
                row.datetime_added,
                row.content,
                row.quality_improvement_category,
                row.get_replacement_string(),
                row.is_rma,
                row.change_status_to,
                row.communication.status.name,
                row.communication.patient.patient_profile.company.name,
                row.resolution.name if row.resolution else ''
            ]
            writer.writerow(output)
        content = output_buffer.getvalue()
        self.download = TemporaryDownload.objects.create(
            for_user=self.requester,
            content=content,
            content_type='text/csv',
            filename='calllog.csv'
        )
