from django import forms

from genesishealth.apps.accounts.models import Message
from genesishealth.apps.utils.forms import GenesisForm, GenesisBatchForm


class NewMessageForm(GenesisForm):
    recipients = forms.ModelMultipleChoiceField(queryset=None,
        widget=forms.CheckboxSelectMultiple)
    subject = forms.CharField(widget=forms.TextInput(attrs={'class': 'required'}))
    content = forms.CharField(widget=forms.Textarea(attrs={'class': 'required'}))

    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester')
        self.to_professional = kwargs.pop('to_professional')

        super(NewMessageForm, self).__init__(*args, **kwargs)

        profile = self.requester.get_profile()
        if self.requester.is_professional():
            if self.to_professional:
                self.fields['recipients'].queryset = profile.get_professionals_in_group() \
                                                     .exclude(pk=self.requester.id)
            else:
                self.fields['recipients'].queryset = profile.get_patients(['send-patient-message'])
        else:
            self.fields['recipients'].queryset = profile.get_professionals()

    def save(self):
        data = self.cleaned_data
        new_message = Message(sender=self.requester, subject=data.get('subject'),
                              content=data.get('content'))
        new_message.save()

        for r in data.get('recipients'):
            new_message.recipients.add(r)

        new_message.send()

        return new_message


class BatchMarkMessageForm(GenesisBatchForm):
    def __init__(self, *args, **kwargs):
        self.read = kwargs.pop('read')
        super(BatchMarkMessageForm, self).__init__(*args, **kwargs)

    def save(self):
        for message_entry in self.batch:
            message_entry.read = self.read
            message_entry.save()
