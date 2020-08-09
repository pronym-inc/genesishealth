from django import forms
from django.contrib.auth.models import User
from django.urls import reverse

from genesishealth.apps.accounts.breadcrumbs.patients import (
    get_patient_breadcrumbs)
from genesishealth.apps.orders.form_fields import SelectProductsField
from genesishealth.apps.orders.models import (
    Order, OrderCategory, ShippingClass)
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.class_views import GenesisFormView
from genesishealth.apps.utils.forms import GenesisForm
from genesishealth.apps.utils.request import require_admin_permission


test = require_admin_permission('orders')


patient_error_messages = {'required': 'You must choose a patient.'}
product_error_messages = {'required': 'You must choose a product.'}


class CreateOrderForm(GenesisForm):
    category = forms.ModelChoiceField(
        queryset=OrderCategory.objects.all())
    products = SelectProductsField(
        error_messages=product_error_messages, required=False)
    notes = forms.CharField(widget=forms.widgets.Textarea, required=False)

    class Media:
        js = ('pages/orders/order_form.js',)

    def __init__(self, *args, **kwargs):
        self.patient = kwargs.pop('patient')
        super(CreateOrderForm, self).__init__(*args, **kwargs)

    def clean(self):
        errors = []
        if not self.cleaned_data['category'].allow_empty_products and not self.cleaned_data['products']:
            errors.append("You must choose at least one product.")
        if errors:
            msg = "\n".join(errors)
            raise forms.ValidationError(msg)
        return self.cleaned_data

    def save(self, commit=True):
        order = Order.objects.create(
            patient=self.patient,
            category=self.cleaned_data['category'],
            order_origin=Order.ORDER_ORIGIN_MANUAL,
            order_notes=self.cleaned_data['notes'],
            order_type=Order.ORDER_TYPE_PATIENT
        )
        for entry in self.cleaned_data['products']:
            entry.order = order
            entry.save()
        self.instance = order
        return order


class CreateForPatientView(GenesisFormView):
    form_class = CreateOrderForm
    template_name = "orders/create_for_patient.html"
    success_message = "The order has been created."
    go_back_until = ['accounts:patient-orders']

    def _get_breadcrumbs(self):
        patient = self.get_patient()
        breadcrumbs = get_patient_breadcrumbs(patient, self.request.user)
        breadcrumbs.append(
            Breadcrumb(
                'Orders',
                reverse('accounts:patient-orders', args=[patient.pk]))
        )
        return breadcrumbs

    def get_form_kwargs(self):
        kwargs = super(CreateForPatientView, self).get_form_kwargs()
        kwargs['patient'] = self.get_patient()
        return kwargs

    def get_patient(self):
        if not hasattr(self, '_patient'):
            self._patient = User.objects.get(
                pk=self.kwargs['patient_id'])
        return self._patient

    def _get_page_title(self):
        return "Create New Order for {0}".format(
            self.get_patient().get_reversed_name())

    def get_success_url(self, form):
        return reverse('orders:details', args=[form.instance.pk])

main = test(CreateForPatientView.as_view())
