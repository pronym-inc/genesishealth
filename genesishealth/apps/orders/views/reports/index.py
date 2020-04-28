from django.views.generic import TemplateView

from genesishealth.apps.utils.request import require_admin_permission


test = require_admin_permission('orders')


class ReportIndexView(TemplateView):
    template_name = 'orders/reports/index.html'


main = test(ReportIndexView.as_view())
