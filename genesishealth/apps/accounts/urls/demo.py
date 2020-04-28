from django.conf.urls import url

from genesishealth.apps.utils.views import generic_dashboard

from genesishealth.apps.accounts.views import demo as views


urlpatterns = [
    url(r'^$',
        views.main,
        name='manage-demo'),
    url(r'^(?P<patient_id>\d+)/$',
        views.edit,
        name='manage-demo-edit'),
    url(r'^edit/thanks/$',
        generic_dashboard,
        {'title': 'Edit Demo Patient',
         'content': 'The demo patient has been updated.'},
        name='manage-demo-edit-thanks'),
    url(r'^new/$',
        views.create,
        name='manage-demo-create'),
    url(r'^new/thanks/$',
        generic_dashboard,
        {'title': 'Create Demo Patient',
         'content': 'The demo patient has been updated.'},
        name='manage-demo-edit-thanks'),
]
