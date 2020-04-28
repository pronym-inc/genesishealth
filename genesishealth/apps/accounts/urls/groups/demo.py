from django.conf.urls import url

from genesishealth.apps.utils.views import generic_dashboard

from genesishealth.apps.accounts.views import demo as views


urlpatterns = [
    url(r'^$',
        views.main,
        name='manage-groups-demo'),
    url(r'^(?P<patient_id>\d+)/$',
        views.edit,
        name='manage-groups-demo-edit'),
    url(r'^edit/thanks/$',
        generic_dashboard,
        {'title': 'Edit Demo Patient',
         'content': 'The demo patient has been updated.'},
        name='manage-groups-demo-edit-thanks'),
    url(r'^new/$',
        views.create,
        name='manage-groups-demo-create'),
    url(r'^new/thanks/$',
        generic_dashboard,
        {'title': 'Create Demo Patient',
         'content': 'The demo patient has been created.'},
        name='manage-groups-demo-create-thanks'),
    url(r'^batch/delete/$',
        views.batch_delete,
        name='manage-groups-demo-batch-delete'),
]
