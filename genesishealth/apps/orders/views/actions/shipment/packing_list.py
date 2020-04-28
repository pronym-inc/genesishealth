from genesishealth.apps.orders.models import Order
from genesishealth.apps.reports.views.main import (
    ReportView, PDFPrintURLResponse)
from genesishealth.apps.utils.request import require_admin_permission


test = require_admin_permission('orders')


class PackingListView(ReportView):
    template_name = 'orders/reports/packing_list.html'
    filename = 'packinglist.pdf'
    response_class = PDFPrintURLResponse

    def get_context_data(self, **kwargs):
        kwargs['order'] = Order.objects.get(
            pk=self.kwargs['order_id'])
        return super(PackingListView, self).get_context_data(
            **kwargs)
main = test(PackingListView.as_view(output_format='html'))
