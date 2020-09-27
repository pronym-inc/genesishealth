from django.conf.urls import url

from genesishealth.apps.accounts.views import companies as views


urlpatterns = [
    url(r'^$',
        views.main,
        name='manage-groups-companies'),
    url(r'^new/$',
        views.add,
        name='manage-groups-companies-create'),
    url(r'^import/$',
        views.import_csv,
        name='manage-groups-companies-import'),
    url(r'^(?P<company_id>\d+?)/$',
        views.edit,
        name='manage-groups-companies-edit'),
    url(r'^(?P<company_id>\d+?)/admin/$',
        views.company_admin,
        name='manage-groups-companies-admin'),
    url(r'^batch/delete/$',
        views.batch_delete,
        name='manage-groups-companies-batch-delete'),
]
