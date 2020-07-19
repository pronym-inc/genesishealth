from datetime import datetime, time, timedelta

from django.utils.timezone import get_default_timezone

from genesishealth.apps.pharmacy.breadcrumbs import get_rx_partner_breadcrumbs
from genesishealth.apps.pharmacy.models import PharmacyPartner
from genesishealth.apps.utils.request import require_admin_permission

from .base_order_history import (
    BaseOrderHistoryReport, BaseOrderHistoryReportView)


test = require_admin_permission('orders')


class RxPartnerOrderHistoryReport(BaseOrderHistoryReport):
    def _configure(self, **kwargs):
        self.rx_partner = PharmacyPartner.objects.get(
            pk=kwargs['rx_partner_id'])

    def get_filename(self, data):
        return "shipping_{0}.csv".format(self.rx_partner.id)

    def get_queryset(self, data):
        tz = get_default_timezone()
        start = tz.localize(datetime.combine(data['start_date'], time()))
        end = tz.localize(
            datetime.combine(data['end_date'], time())) + timedelta(days=1)
        return self.rx_partner.orders_to_fulfill.filter(
            datetime_added__range=(start, end)).order_by(
            'datetime_added')


class RxPartnerOrderHistoryReportView(BaseOrderHistoryReportView):
    report_class = RxPartnerOrderHistoryReport

    def _get_breadcrumbs(self):
        return get_rx_partner_breadcrumbs(
            self.get_rx_partner(), self.request.user)

    def _get_page_title(self):
        return "Generate Order History For {0}".format(
            self.get_rx_partner().name)

    def _get_report_kwargs(self):
        data = super(RxPartnerOrderHistoryReportView, self)._get_report_kwargs()
        data['rx_partner_id'] = self.kwargs['rx_partner_id']
        return data

    def get_rx_partner(self):
        if not hasattr(self, '_rx_partner'):
            self._rx_partner = PharmacyPartner.objects.get(
                id=self.kwargs['rx_partner_id'])
        return self._rx_partner


main = test(RxPartnerOrderHistoryReportView.as_view())
