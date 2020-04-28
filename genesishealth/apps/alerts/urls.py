from django.conf.urls import url

from genesishealth.apps.utils.views import generic_dashboard
from genesishealth.apps.alerts.views import main as views

urlpatterns = [
    url(r'^$',
        views.main,
        name='alerts'),
    url(r'^patients/$',
        views.main,
        {'filter_type': 'for-my-patients'},
        name='alerts-patients'),
    url(r'^new/$',
        views.new,
        name='alerts-new'),
    url(r'^new/thanks/$',
        generic_dashboard,
        {'title': 'Add Alert', 'content': 'The alert has been created.'},
        name='alerts-new-thanks'),
    url(r'^edit/(?P<alert_id>\d+)/$',
        views.edit,
        name='alerts-edit'),
    url(r'^edit/thanks/$',
        generic_dashboard,
        {'title': 'Edit Alert', 'content': 'The alert has been updated.'},
        name='alerts-edit-thanks'),
    url(r'^batch/disable/$',
        views.batch_change_status,
        {'enable': False},
        name='batch-disable'),
    url(r'^batch/enable/$',
        views.batch_change_status,
        {'enable': True},
        name='batch-enable'),
    url(r'^batch/delete/$',
        views.batch_delete,
        name='batch-delete'),
]
