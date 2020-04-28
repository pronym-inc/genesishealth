from django.conf.urls import url

from genesishealth.apps.accounts.views import payors as views


urlpatterns = [
    url(r'^$',
        views.PayorTableView.as_view(),
        name='manage-payors'),
    url(r'^new/$',
        views.add,
        name='manage-payors-create'),
    url(r'^(?P<payor_id>\d+?)/$',
        views.edit,
        name='manage-payors-edit'),
    url(r'^batch/delete/$',
        views.batch_delete,
        name='manage-payors-batch-delete'),
    url(r'^import/$',
        views.import_csv,
        name='manage-payors-import'),
]
