from django import forms

from genesishealth.apps.orders.breadcrumbs import get_order_breadcrumbs
from genesishealth.apps.orders.models import Order
from genesishealth.apps.utils.class_views import GenesisFormView
from genesishealth.apps.utils.forms import GenesisForm
from genesishealth.apps.utils.request import require_admin_permission


test = require_admin_permission('orders')


class ResolveProblemForm(GenesisForm):
    resolution_description = forms.CharField(widget=forms.widgets.Textarea)

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order')
        self.requester = kwargs.pop('requester')
        super(ResolveProblemForm, self).__init__(*args, **kwargs)

    def clean(self):
        if not self.order.can_resolve_problem():
            raise forms.ValidationError(
                "This order cannot be resolved.")
        return self.cleaned_data

    def save(self):
        self.order.resolve_problem(
            self.cleaned_data['resolution_description'], self.requester)


class ResolveProblemView(GenesisFormView):
    form_class = ResolveProblemForm
    go_back_until = ['orders:index']
    success_message = "The order's problem has been resolved."

    def get_breadcrumbs(self):
        return get_order_breadcrumbs(self.get_order(), self.request.user)

    def get_form_kwargs(self):
        kwargs = super(ResolveProblemView, self).get_form_kwargs()
        kwargs['order'] = self.get_order()
        kwargs['requester'] = self.request.user
        return kwargs

    def get_order(self):
        if not hasattr(self, '_order'):
            self._order = Order.objects.get(pk=self.kwargs['order_id'])
        return self._order

    def get_page_title(self):
        order = self.get_order()
        if order.is_patient_order():
            for_label = order.patient.get_reversed_name()
        else:
            for_label = order.rx_partner.name
        return "Resolve Problem for Order #{0} for {1}".format(
            order.id, for_label)
main = test(ResolveProblemView.as_view())
