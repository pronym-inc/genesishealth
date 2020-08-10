from django.views.generic import TemplateView

from genesishealth.apps.utils.request import require_admin_permission


test = require_admin_permission('orders')


class AdminIndexView(TemplateView):
    template_name = 'ghtadmin/admin/index.html'


main = test(AdminIndexView.as_view())
