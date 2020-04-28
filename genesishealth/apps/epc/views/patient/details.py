from django import forms

from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse

from genesishealth.apps.accounts.breadcrumbs.patients import (
    get_patient_breadcrumbs)
from genesishealth.apps.epc.models import EPCOrder, EPCOrderNote
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.class_views import GenesisFormView
from genesishealth.apps.utils.forms import GenesisForm

from genesishealth.apps.utils.request import admin_user


admin_test = user_passes_test(admin_user)


class OrderNoteForm(GenesisForm):
    message = forms.CharField(widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order')
        self.requester = kwargs.pop('requester')
        super(OrderNoteForm, self).__init__(*args, **kwargs)

    def save(self):
        message = self.cleaned_data['message']
        note = EPCOrderNote.objects.create(
            order=self.order,
            message=message,
            added_by=self.requester
        )
        return note


class OrderDetailsView(GenesisFormView):
    form_class = OrderNoteForm
    go_back_until = ['epc:patient-order-details']
    success_message = 'The note has been added to the order.'
    template_name = 'epc/patient/details.html'

    def get_breadcrumbs(self):
        patient = self.get_order().epc_member.user
        breadcrumbs = get_patient_breadcrumbs(
            patient, self.request.user, include_detail=True)
        breadcrumbs.append(
            Breadcrumb(
                'EPC Orders', reverse('epc:patient-orders', args=[patient.pk]))
        )
        return breadcrumbs

    def get_context_data(self, **kwargs):
        kwargs['order'] = self.get_order()
        return super(OrderDetailsView, self).get_context_data(**kwargs)

    def get_form_kwargs(self):
        kwargs = super(OrderDetailsView, self).get_form_kwargs()
        kwargs['requester'] = self.request.user
        kwargs['order'] = self.get_order()
        return kwargs

    def get_order(self):
        if not hasattr(self, '_order'):
            self._order = EPCOrder.objects.get(
                pk=self.kwargs['order_id'])
        return self._order

    def get_page_title(self):
        order = self.get_order()
        return 'Manage Order {0} for {1}'.format(
            order.order_number,
            order.epc_member.user.get_reversed_name())

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


details = login_required(
    admin_test(OrderDetailsView.as_view()))
