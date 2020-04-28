from django.conf.urls import url

from genesishealth.apps.accounts.views import companies as views


urlpatterns = [
    url(r'^$',
        views.main,
        name='manage-companies'),
    url(r'^new/$',
        views.add,
        name='manage-companies-create'),
    url(r'^(?P<company_id>\d+?)/$',
        views.edit,
        name='manage-companies-edit'),
    url(r'^batch/delete/$',
        views.batch_delete,
        name='manage-companies-batch-delete'),
    url(r'^import/$',
        views.import_csv,
        name='manage-companies-import'),
]
