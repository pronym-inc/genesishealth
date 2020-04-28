from django.contrib.auth.decorators import login_required, user_passes_test

from genesishealth.apps.utils.request import admin_user

from .log import EPCLogEntryTableView


admin_test = user_passes_test(admin_user)


class EPCErrorLogEntryTableView(EPCLogEntryTableView):
    def get_queryset(self):
        qs = EPCLogEntryTableView.get_queryset(self)
        return qs.filter(is_successful=False)


error_log_table = login_required(
    admin_test(EPCErrorLogEntryTableView.as_view()))
