from django.conf.urls import url

from genesishealth.apps.utils.views import generic_dashboard

from genesishealth.apps.accounts.views import patients as views


urlpatterns = [
    url(r'^$',
        views.main,
        name='manage-groups-patients'),
    url(r'^assigned/$',
        views.main,
        {'show_assigned': True},
        name='manage-groups-patients-assigned'),
    url(r'^new/$',
        views.add,
        name='manage-groups-patients-create'),
    url(r'^import/$',
        views.import_csv,
        name='manage-groups-patients-import'),
    url(r'^(?P<patient_id>\d+?)/$',
        views.edit,
        name='manage-groups-patients-edit'),
    url(r'^edit/thanks/$',
        generic_dashboard,
        {'title': 'Edit Patient',
         'content': 'The patient has been updated.'},
        name='manage-groups-patients-edit-thanks'),
    url(r'^new/thanks/$',
        generic_dashboard,
        {'title': 'Add Patient',
         'content': 'The patient has been created.'},
        name='manage-groups-patients-create-thanks'),
    url(r'^batch/assign/$',
        views.batch_assign,
        name='manage-groups-patients-batch-assign'),
    url(r'^batch/unassign/$',
        views.batch_unassign,
        name='manage-groups-patients-batch-unassign'),
]
