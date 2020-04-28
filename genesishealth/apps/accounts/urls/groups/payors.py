from django.conf.urls import url

from genesishealth.apps.accounts.views import payors as views


urlpatterns = [
    url(r'^$',
        views.main,
        name='manage-groups-payors'),
    url(r'^new/$',
        views.add,
        name='manage-groups-payors-create'),
    url(r'^import/$',
        views.import_csv,
        name='manage-groups-payors-import'),
    url(r'^(?P<payor_id>\d+?)/$',
        views.edit,
        name='manage-groups-payors-edit'),
    url(r'^batch/delete/$',
        views.batch_delete,
        name='manage-groups-payors-batch-delete'),
]
