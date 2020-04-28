from genesishealth.apps.orders.breadcrumbs import get_order_breadcrumbs
from genesishealth.apps.orders.models import Order, OrderProblem
from genesishealth.apps.utils.class_views import GenesisFormView
from genesishealth.apps.utils.forms import GenesisModelForm
from genesishealth.apps.utils.request import require_admin_permission


test = require_admin_permission('orders')


class OrderProblemForm(GenesisModelForm):
    class Meta:
        model = OrderProblem
        fields = ('category', 'description')

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order')
        self.requester = kwargs.pop('requester')
        super(OrderProblemForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.iteritems():
            field.required = False

    def save(self):
        obj = super(OrderProblemForm, self).save(commit=False)
        self.order.add_problem(
            obj.category,
            obj.description,
            self.requester)
        return obj


class CreateOrderProblemView(GenesisFormView):
    form_class = OrderProblemForm
    go_back_until = ['orders:details']
    success_message = "The problem has been added to the order."

    def get_breadcrumbs(self):
        return get_order_breadcrumbs(self.get_order(), self.request.user)

    def get_form_kwargs(self):
        kwargs = super(CreateOrderProblemView, self).get_form_kwargs()
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
        return "Create Problem for Order #{0} for {1}".format(
            self.get_order().id, for_label)
main = test(CreateOrderProblemView.as_view())
