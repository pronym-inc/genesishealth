from datetime import datetime, time, timedelta

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.timezone import get_default_timezone

from genesishealth.apps.accounts.breadcrumbs.patients import (
    get_patient_breadcrumbs)
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.request import require_admin_permission

from .base_order_history import (
    BaseOrderHistoryReport, BaseOrderHistoryReportView)


test = require_admin_permission('orders')


class PatientOrderHistoryReport(BaseOrderHistoryReport):
    def configure(self, **kwargs):
        self.patient = User.objects.get(
            pk=kwargs['patient_id'])

    def get_filename(self, data):
        return "shipping_{0}.csv".format(self.patient.id)

    def get_queryset(self, data):
        tz = get_default_timezone()
        start = tz.localize(datetime.combine(data['start_date'], time()))
        end = tz.localize(
            datetime.combine(data['end_date'], time())) + timedelta(days=1)
        return self.patient.orders.filter(
            datetime_added__range=(start, end)).order_by(
                'datetime_added')


class PatientOrderHistoryReportView(BaseOrderHistoryReportView):
    report_class = PatientOrderHistoryReport

    def get_breadcrumbs(self):
        user = self.get_patient()
        breadcrumbs = get_patient_breadcrumbs(user, self.request.user)
        breadcrumbs.append(
            Breadcrumb('Reports',
                       reverse('reports:patient-index', args=[user.pk])))
        return breadcrumbs

    def get_page_title(self):
        return "Generate Order History For {0}".format(
            self.get_patient().get_reversed_name())

    def get_patient(self):
        if not hasattr(self, '_patient'):
            self._patient = User.objects.filter(
                patient_profile__isnull=False).get(
                id=self.kwargs['patient_id'])
        return self._patient

    def get_report_kwargs(self):
        data = super(PatientOrderHistoryReportView, self).get_report_kwargs()
        data['patient_id'] = self.kwargs['patient_id']
        return data


main = test(PatientOrderHistoryReportView.as_view())
