from django.conf.urls import url
from django.views.generic import TemplateView

from genesishealth.apps.utils.views import generic_dashboard
from genesishealth.apps.accounts.views import professionals as prof_views


urlpatterns = [
    url(r'^$',
        prof_views.main,
        name='manage-professionals'),
    url(r'^(?P<user_id>\d+?)/$',
        prof_views.edit,
        name='manage-professionals-edit'),
    url(r'^(?P<user_id>\d+?)/detail/$',
        prof_views.detail,
        name='manage-professionals-detail'),
    url(r'^(?P<user_id>\d+?)/patients/$',
        prof_views.manage_caregiver_patients,
        name='manage-professionals-patients'),
    url(r'^(?P<user_id>\d+?)/patients/assigned/$',
        prof_views.manage_caregiver_patients,
        {'show_assigned': True},
        name='manage-professionals-patients-assigned'),
    url(r'^(?P<user_id>\d+?)/patients/batch_assign/$',
        prof_views.manage_caregiver_patients_batch_assign,
        name='manage-professionals-patients-batch-assign'),
    url(r'^(?P<user_id>\d+?)/patients/batch_unassign/$',
        prof_views.manage_caregiver_patients_batch_unassign,
        name='manage-professionals-patients-batch-unassign'),
    url(r'^edit/thanks/$',
        TemplateView.as_view(
            template_name='accounts/manage/edit-professional-thanks.html'),
        name='manage-professionals-edit-thanks'),
    url(r'^new/$',
        prof_views.add,
        name='manage-professionals-create'),
    url(r'^new/thanks/$',
        generic_dashboard,
        {'title': 'Add Professional',
         'content': 'The professional has been created.'},
        name='manage-professionals-create-thanks'),
    url(r'^batch/delete/$',
        prof_views.batch_delete,
        name='manage-professionals-batch-delete'),
    url(r'^import/$',
        prof_views.import_csv,
        name='manage-professionals-import'),
    url(r'^caregivers/$',
        prof_views.main,
        {'caregivers': True},
        name='manage-caregivers'),
    url(r'^professional_reports/noncompliant/$',
        prof_views.professional_noncompliant_report,
        name='professional-noncompliant-report'),
    url(r'^professional_reports/target/$',
        prof_views.professional_target_range_report,
        name='professional-target-range-report')
]
