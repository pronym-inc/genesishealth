from django import forms

from genesishealth.apps.readings.models import GlucoseReading


class ReadingNoteForm(forms.ModelForm):
    notes = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = GlucoseReading
        fields = ('notes',)