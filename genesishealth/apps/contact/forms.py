from django.contrib.auth.models import AnonymousUser

from genesishealth.apps.utils.forms import GenesisModelForm
from genesishealth.apps.contact.models import ContactFormSubmission


class ContactForm(GenesisModelForm):
    class Meta:
        model = ContactFormSubmission
        fields = ('name', 'email', 'subject', 'content')

    def __init__(self, *args, **kwargs):
        requester = kwargs.pop('requester')
        super(ContactForm, self).__init__(*args, **kwargs)
        if requester and not isinstance(requester, AnonymousUser):
            self.fields['name'].initial = requester.get_full_name()
            self.fields['email'].initial = requester.email

    def save(self):
        instance = super(ContactForm, self).save()
        instance.send_email()
