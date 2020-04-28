from django import forms

from genesishealth.apps.alerts.models import (
    ProfessionalAlert, PatientAlert, AlertTemplate)
from genesishealth.apps.utils.forms import (
    GenesisForm, GenesisModelForm, GenesisBatchForm)


class ProfessionalAlertForm(GenesisForm):
    CONTACT_TEXT, CONTACT_EMAIL, CONTACT_APP = (
        ProfessionalAlert.CONTACT_METHODS)

    CONTACT_METHOD_CHOICES = (
        (CONTACT_TEXT, 'Text Message'),
        (CONTACT_EMAIL, 'Email'),
        (CONTACT_APP, 'Phone App')
    )

    name = forms.CharField()
    template = forms.ModelChoiceField(
        required=False, queryset=None,
        help_text='Leave blank to create a customized form.')
    recipient_type = forms.ChoiceField(
        choices=ProfessionalAlert.RECIPIENT_TYPE_CHOICES,
        initial=ProfessionalAlert.PROFESSIONAL_RECIPIENT)
    type = forms.ChoiceField(
        required=False, choices=ProfessionalAlert.TYPE_CHOICES)
    professionals = forms.ModelMultipleChoiceField(
        label="Users to notify", queryset=None,
        required=False, widget=forms.CheckboxSelectMultiple)
    contact_methods = forms.MultipleChoiceField(
        choices=CONTACT_METHOD_CHOICES,
        widget=forms.CheckboxSelectMultiple)
    message = forms.CharField(widget=forms.Textarea())
    patients = forms.ModelMultipleChoiceField(
        queryset=None, widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester')
        super(ProfessionalAlertForm, self).__init__(*args, **kwargs)
        self.fields['professionals'].queryset = self.requester\
            .professional_profile.parent_group.get_professionals(
                ['view-alerts'])
        self.fields['patients'].queryset = self.requester\
            .professional_profile.get_patients(['add-alerts'])
        self.fields['template'].queryset = self.requester\
            .professional_profile.parent_group.alert_templates.filter(
                enabled=True)

    def clean(self):
        data = self.cleaned_data
        if (data.get('recipient_type') ==
                ProfessionalAlert.PROFESSIONAL_RECIPIENT and
                len(data.get('professionals')) == 0):
            raise forms.ValidationError(
                'You must specify at least one professional to receive '
                'this alert.')
        return data

    def save(self, patients=None, *args, **kwargs):
        data = self.cleaned_data
        alert_kwargs = {
            'group': self.requester.professional_profile.parent_group,
            'created_by': self.requester}
        patients = patients or data.get('patients')

        data_fields = ('template', 'type', 'message', 'recipient_type')
        for df in data_fields:
            alert_kwargs[df] = data.get(df)

        for cm in data.get('contact_methods'):
            alert_kwargs[cm] = True

        for patient in patients:
            alert_name = "{} for {}".format(
                data.get('name'), patient.get_full_name())
            new_alert = ProfessionalAlert(
                patient=patient, name=alert_name, **alert_kwargs)
            new_alert.save()
            if (new_alert.recipient_type ==
                    ProfessionalAlert.PROFESSIONAL_RECIPIENT):
                for professional in data.get('professionals'):
                    new_alert.professionals.add(professional)


class ProfessionalBatchAlertForm(ProfessionalAlertForm, GenesisBatchForm):
    def __init__(self, *args, **kwargs):
        super(ProfessionalBatchAlertForm, self).__init__(*args, **kwargs)
        del self.fields['patients']

    def save(self):
        super(ProfessionalBatchAlertForm, self).save(patients=self.batch)


class ProfessionalEditAlertForm(GenesisForm):
    name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'required'}),
        help_text='System will append "for (patient)" to the end of each '
        'created alert.')
    type = forms.ChoiceField(
        required=False, choices=ProfessionalAlert.TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'required'}))
    professionals = forms.ModelMultipleChoiceField(
        label="Users to notify", queryset=None,
        required=False, widget=forms.CheckboxSelectMultiple)
    contact_methods = forms.MultipleChoiceField(
        required=False,
        choices=ProfessionalBatchAlertForm.CONTACT_METHOD_CHOICES,
        widget=forms.CheckboxSelectMultiple)
    message = forms.CharField(required=False, widget=forms.Textarea())

    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester')
        self.alert = kwargs.pop('instance')
        super(ProfessionalEditAlertForm, self).__init__(*args, **kwargs)
        self.fields['professionals'].queryset = self.requester\
            .professional_profile.parent_group.get_professionals(
                ['view-alerts'])
        for field_name in ('name', 'type', 'message'):
            self.fields[field_name].initial = getattr(self.alert, field_name)
        initial_contact_methods = []
        for k, v in ProfessionalAlertForm.CONTACT_METHOD_CHOICES:
            if getattr(self.alert, k):
                initial_contact_methods.append(k)
        self.fields['professionals'].initial = self.alert.professionals.all()
        self.fields['contact_methods'].initial = initial_contact_methods

    def clean(self):
        data = self.cleaned_data
        if (data.get('recipient_type') ==
                ProfessionalAlert.PROFESSIONAL_RECIPIENT and
                len(data.get('professionals')) == 0):
            raise forms.ValidationError(
                'You must specify at least one professional to '
                'receive this alert.')
        return data

    def save(self, *args, **kwargs):
        data = self.cleaned_data

        self.alert.name = data.get('name')
        self.alert.type = data.get('type')
        self.alert.message = data.get('message')

        for cm in ProfessionalAlert.CONTACT_METHODS:
            setattr(self.alert, cm, cm in data.get('contact_methods'))

        self.alert.save()

        self.alert.professionals.clear()
        for p in data.get('professionals'):
            self.alert.professionals.add(p)

        return self.alert


class PatientAlertForm(GenesisModelForm):
    phone_number = forms.CharField(required=False)
    email = forms.EmailField(required=False)

    class Meta:
        model = PatientAlert
        fields = ('name', 'phone_number', 'email')

    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester')
        super(PatientAlertForm, self).__init__(*args, **kwargs)

    def clean(self):
        data = self.cleaned_data
        if not data.get('phone_number') and not data.get('email'):
            raise forms.ValidationError(
                'You must provide at least one phone number or email.')
        return data

    def save(self):
        if self.is_new:
            alert = super(type(self), self).save(commit=False)
            alert.created_by = alert.patient = self.requester
            alert.save()
        else:
            alert = super(type(self), self).save()

        return alert


class AlertTemplateForm(GenesisModelForm):
    contact_methods = forms.MultipleChoiceField(
        choices=ProfessionalBatchAlertForm.CONTACT_METHOD_CHOICES,
        widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = AlertTemplate
        fields = (
            'name', 'type', 'recipient_type', 'contact_methods', 'message')

    def __init__(self, *args, **kwargs):
        self.requester = kwargs['requester']
        del kwargs['requester']
        super(AlertTemplateForm, self).__init__(*args, **kwargs)
        self.fields['recipient_type'].choices = ProfessionalAlert\
            .RECIPIENT_TYPE_CHOICES
        self.fields['type'].choices = ProfessionalAlert.TYPE_CHOICES

    def save(self, *args, **kwargs):
        data = self.cleaned_data
        template = super(AlertTemplateForm, self).save(
            commit=False, *args, **kwargs)
        template.group = self.requester.professional_profile.parent_group

        contact_methods = data.get('contact_methods')
        template.send_by_text = 'text' in contact_methods
        template.send_by_email = 'email' in contact_methods
        template.send_by_message = 'message' in contact_methods
        template.send_by_app = 'app' in contact_methods

        template.save()

        return template


class EditAlertTemplateForm(GenesisForm):
    name = forms.CharField()
    type = forms.ChoiceField(choices=ProfessionalAlert.TYPE_CHOICES)
    recipient_type = forms.ChoiceField(
        choices=ProfessionalAlert.RECIPIENT_TYPE_CHOICES)
    contact_methods = forms.MultipleChoiceField(
        choices=ProfessionalBatchAlertForm.CONTACT_METHOD_CHOICES,
        widget=forms.CheckboxSelectMultiple)
    message = forms.CharField(widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester')
        self.template = kwargs.pop('template')
        super(EditAlertTemplateForm, self).__init__(*args, **kwargs)
        for field_name in ('name', 'type', 'recipient_type', 'message'):
            self.fields[field_name].initial = getattr(
                self.template, field_name)
        initial_contact_methods = []
        for k, v in ProfessionalBatchAlertForm.CONTACT_METHOD_CHOICES:
            if getattr(self.template, k):
                initial_contact_methods.append(k)
        self.fields['contact_methods'].initial = initial_contact_methods

    def clean_name(self):
        name = self.cleaned_data.get('name')
        try:
            self.requester.professional_profile\
                .parent_group.alert_templates.exclude(pk=self.template.id).get(
                    name=name)
        except AlertTemplate.DoesNotExist:
            pass
        else:
            raise forms.ValidationError(
                'An alert template with that name already exists.  '
                'Please choose another name.')
        return name

    def save(self):
        data = self.cleaned_data
        for field_name in ('name', 'type', 'recipient_type', 'message'):
            setattr(
                self.template, field_name, self.cleaned_data.get(field_name))

        contact_methods = data.get('contact_methods')
        for k, v in ProfessionalBatchAlertForm.CONTACT_METHOD_CHOICES:
            setattr(self.template, k, k in contact_methods)

        self.template.save()
        return self.template


class BatchEnableDisableForm(GenesisBatchForm):
    def __init__(self, *args, **kwargs):
        self.enable = kwargs.pop('enable')
        super(BatchEnableDisableForm, self).__init__(*args, **kwargs)

    def save(self):
        for alert in self.batch:
            alert.active = self.enable
            alert.save()
