from django.conf.urls import url
from django.views.generic import TemplateView

from genesishealth.apps.utils.views import generic_dashboard

from genesishealth.apps.accounts.views import professionals as views


urlpatterns = [
    url(r'^$',
        views.main,
        name='manage-groups-professionals'),
    url(r'^new/$',
        views.add,
        name='manage-groups-professionals-create'),
    url(r'^new/thanks/$',
        generic_dashboard,
        {'title': 'Add Professional',
         'content': 'The professional has been created.'},
        name='manage-groups-professionals-create-thanks'),
    url(r'^import/$',
        views.import_csv,
        name='manage-groups-professionals-import'),
    url(r'^batch/delete/$',
        views.batch_delete,
        name='manage-groups-professionals-batch-delete'),
    url(r'^(?P<user_id>\d+?)/$',
        views.edit,
        name='manage-groups-professionals-edit'),
    url(r'^edit/thanks/$',
        TemplateView.as_view(
            template_name='accounts/manage/edit-professional-thanks.html'),
        name='manage-groups-professionals-edit-thanks'),
    url(r'^professional_reports/noncompliant/$',
        views.professional_noncompliant_report,
        name='professional-noncompliant-report'),
]
