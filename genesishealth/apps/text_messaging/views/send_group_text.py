from django import forms
from django.contrib.auth.models import User
from django.urls import reverse

from genesishealth.apps.accounts.models import Company
from genesishealth.apps.text_messaging.func import ConnectionsAPIClient
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.class_views import GenesisFormView
from genesishealth.apps.utils.forms import GenesisForm
from genesishealth.apps.utils.request import require_admin_permission


class SendGroupTextForm(GenesisForm):
    message = forms.CharField()


class SendGroupTextView(GenesisFormView):
    form_class = SendGroupTextForm
    go_back_until = ['accounts:manage-groups-companies']
    success_message = "The text message has been sent."

    def _get_breadcrumbs(self):
        group = self.get_company().group
        return [
            Breadcrumb('Business Partners',
                       reverse('accounts:manage-groups')),
            Breadcrumb(
                'Business Partner: {0}'.format(group.name),
                reverse('accounts:manage-groups-detail',
                        args=[group.pk])),
            Breadcrumb(
                'Companies',
                reverse('accounts:manage-groups-companies',
                        args=[group.pk]))
        ]

    def get_company(self):
        if not hasattr(self, '_company'):
            self._company = Company.objects.get(pk=self.kwargs['company_id'])
        return self._company

    def _get_page_title(self):
        return "Send Group Text Message to {0}".format(self.get_company().name)

    def get_success_url(self, form):
        group = self.get_company().group
        return reverse('accounts:manage-groups-companies', args=[group.pk])

    def save_form(self, form):
        # Send text to each member of the company.
        recipients = User.objects.filter(
            patient_profile__company=self.get_company())
        client = ConnectionsAPIClient()
        client.send_text(form.cleaned_data['message'], recipients)


test = require_admin_permission('manage-business-partners')
main = test(SendGroupTextView.as_view())
