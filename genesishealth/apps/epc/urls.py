from django.conf.urls import include, url

from genesishealth.apps.epc.views.api import (
    OrderRequestTransactionResource,
    PatientRequestTransactionResource)
from genesishealth.apps.epc.views.groups.export import group_export
from genesishealth.apps.epc.views.logs import (
    error_log_table, order_log, patient_log, log_table)
from genesishealth.apps.epc.views.patient import (
    details, patient_orders)


urlpatterns = [
    url(r'^patient/',
        include(PatientRequestTransactionResource.urls())),
    url(r'^order/',
        include(OrderRequestTransactionResource.urls())),
    url(r'^order_log/$', order_log, name="order-log"),
    url(r'^patient_log/$', patient_log, name="patient-log"),
    url(r'^orders/(?P<patient_id>\d+)/$',
        patient_orders,
        name="patient-orders"),
    url(r'^orders/details/(?P<order_id>\d+)/$',
        details,
        name="patient-orders-details"),
    url(r'^log/$',
        log_table,
        name='log'),
    url(r'^error_log/$',
        error_log_table,
        name='error-log'),
    url(r'group_export/(?P<group_id>\d+)/$',
        group_export,
        name='group-export')
]
