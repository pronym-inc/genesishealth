from collections import OrderedDict
from datetime import datetime, timedelta

from django import forms

from genesishealth.apps.accounts.models import PatientProfile
from genesishealth.apps.utils.forms import GenesisForm
from genesishealth.apps.utils.func import utcnow


class SingleChartControlForm(GenesisForm):
    '''
    Simpler generic form used for query of the whole chart; all four charts.
    '''
    DAYS_CHOICES = (
        (1, '1'), (7, '7'), (14, '14'), (30, '30'), (60, '60'),
        (90, '90'), ('custom', 'custom'))
    days = forms.ChoiceField(widget=forms.HiddenInput, choices=DAYS_CHOICES)
    start_date = forms.DateField(widget=forms.HiddenInput)
    end_date = forms.DateField(widget=forms.HiddenInput)

    def get_date(self, date_key):
        return datetime.strptime(self.data[date_key], "%m/%d/%Y")


class MultiChartControlForm(GenesisForm):
    DAYS_CHOICES = (
        (1, '1'), (7, '7'), (14, '14'), (30, '30'), (60, '60'),
        (90, '90'), ('custom', 'custom'))
    premeal_days = forms.ChoiceField(
        widget=forms.HiddenInput, choices=DAYS_CHOICES)
    premeal_start_date = forms.DateField(widget=forms.HiddenInput)
    premeal_end_date = forms.DateField(widget=forms.HiddenInput)
    postmeal_days = forms.ChoiceField(
        widget=forms.HiddenInput, choices=DAYS_CHOICES)
    postmeal_start_date = forms.DateField(widget=forms.HiddenInput)
    postmeal_end_date = forms.DateField(widget=forms.HiddenInput)
    combined_days = forms.ChoiceField(
        widget=forms.HiddenInput, choices=DAYS_CHOICES)
    combined_start_date = forms.DateField(widget=forms.HiddenInput)
    combined_end_date = forms.DateField(widget=forms.HiddenInput)
    summary_days = forms.ChoiceField(
        widget=forms.HiddenInput, choices=DAYS_CHOICES)
    summary_start_date = forms.DateField(widget=forms.HiddenInput)
    summary_end_date = forms.DateField(widget=forms.HiddenInput)

    def get_date(self, date_key):
        return datetime.strptime(self.data[date_key], "%m/%d/%Y")


class ReportForm(GenesisForm):
    REPORT_TYPE_CHOICE_PREMEAL = 'premeal'
    REPORT_TYPE_CHOICE_POSTMEAL = 'postmeal'
    REPORT_TYPE_CHOICE_COMBINED = 'combined'
    REPORT_TYPE_CHOICES = (
        (REPORT_TYPE_CHOICE_PREMEAL, 'Pre-Meal'),
        (REPORT_TYPE_CHOICE_POSTMEAL, 'Post-Meal'),
        (REPORT_TYPE_CHOICE_COMBINED, 'Combined'),
    )

    start_date = forms.DateField()
    end_date = forms.DateField()
    type = forms.ChoiceField(choices=REPORT_TYPE_CHOICES, required=False)

    def get_date(self, date_key):
        return datetime.strptime(self.data[date_key], "%m/%d/%Y")


class DisplayLogbookForm(GenesisForm):
    patient = forms.ModelChoiceField(
        queryset=PatientProfile.myghr_patients.get_users(),
        widget=forms.HiddenInput)
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'hidden'}))
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'hidden'}))
    display_type = forms.ChoiceField(
        choices=(('logbook4', '4 Columns'),
                 ('logbook8', '8 Columns')),
        initial='logbook4')

    def __init__(self, *args, **kwargs):
        self.patient = kwargs.pop('patient', None)
        self.requester = kwargs.pop('requester', None)
        super(DisplayLogbookForm, self).__init__(*args, **kwargs)
        if self.patient:
            self.fields['patient'].queryset = PatientProfile.myghr_patients.get_users().filter(pk=self.patient.id)
            self.fields['patient'].initial = self.patient
            self.fields['start_date'].initial = \
                utcnow().astimezone(
                    self.patient.patient_profile.timezone) - timedelta(days=14)
            self.fields['end_date'].initial = \
                utcnow().astimezone(self.patient.patient_profile.timezone)

    def clean_patient(self):
        if self.patient:
            return self.patient
        return self.cleaned_data.get('patient')


class BaseEntryForm(GenesisForm):
    """
    Form displays readonly information about the entry and then has a notes
    form.
    """
    note = forms.CharField(widget=forms.Textarea, label='Your notes')

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance')
        self.requester = kwargs.pop('requester')
        super(GenesisForm, self).__init__(*args, **kwargs)
        existing_note = self.instance.get_note_for_user(self.requester)
        if existing_note:
            self.fields['note'].initial = existing_note.content

        for field in self.Meta.object_fields:
            form_field = self.instance._meta.get_field(field).formfield
            widget_class = form_field().widget.__class__
            attrs = {'readonly': 'readonly'}
            self.fields[field] = form_field(
                widget=widget_class(attrs=attrs),
                initial=getattr(self.instance, field),
                required=False)
        for field in self.Meta.readonly_fields:
            self.fields[field].widget.attrs['readonly'] = 'readonly'
        # Move note to the bottom.  It's always first by default.
        self.fields = OrderedDict(
            self.fields.items()[1:] +
            self.fields.items()[:1]
        )

    def save(self):
        self.instance.set_note_for_user(self.requester,
                                        self.cleaned_data.get('note'))


class GlucoseReadingEntryForm(BaseEntryForm):
    reading_datetime = forms.CharField(label='Reading datetime')

    class Meta:
        object_fields = ('glucose_value', )
        readonly_fields = ('reading_datetime',)

    def __init__(self, *args, **kwargs):
        super(GlucoseReadingEntryForm, self).__init__(*args, **kwargs)
        self.fields['reading_datetime'].initial = self.instance\
            .reading_datetime.strftime('%m/%d/%Y %I:%M %p')
