from datetime import datetime, time, timedelta

from django.urls import reverse
from django.utils.timezone import get_default_timezone

from genesishealth.apps.accounts.models import GenesisGroup
from genesishealth.apps.orders.models import Order
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.request import require_admin_permission

from .base_order_history import (
    BaseOrderHistoryReport, BaseOrderHistoryReportView)


test = require_admin_permission('orders')


class BusinessPartnerOrderHistoryReport(BaseOrderHistoryReport):
    def _configure(self, **kwargs):
        self.partner = GenesisGroup.objects.get(
            pk=kwargs['partner_id'])

    def get_filename(self, data):
        return "shipping_{0}.csv".format(self.partner.id)

    def get_queryset(self, data):
        tz = get_default_timezone()
        start = tz.localize(datetime.combine(data['start_date'], time()))
        end = tz.localize(
            datetime.combine(data['end_date'], time())) + timedelta(days=1)
        return Order.objects.filter(
            patient__patient_profile__group=self.partner,
            datetime_added__range=(start, end)).order_by('datetime_added')


class BusinessPartnerOrderHistoryReportView(BaseOrderHistoryReportView):
    report_class = BusinessPartnerOrderHistoryReport

    def _get_breadcrumbs(self):
        group = self.get_partner()
        breadcrumbs = [
            Breadcrumb('Business Partners',
                       reverse('accounts:manage-groups')),
            Breadcrumb(
                'Business Partner: {0}'.format(group.name),
                reverse('accounts:manage-groups-detail',
                        args=[group.pk])),
            Breadcrumb(
                'Reports',
                reverse('accounts:manage-groups-reports',
                        args=[group.pk]))
        ]
        return breadcrumbs

    def _get_page_title(self):
        return "Generate Order History For {0}".format(
            self.get_partner().name)

    def get_partner(self):
        if not hasattr(self, '_partner'):
            self._partner = GenesisGroup.objects.get(
                id=self.kwargs['partner_id'])
        return self._partner

    def _get_report_kwargs(self):
        data = super(BusinessPartnerOrderHistoryReportView, self)\
            ._get_report_kwargs()
        data['partner_id'] = self.kwargs['partner_id']
        return data


main = test(BusinessPartnerOrderHistoryReportView.as_view())
