from django.conf.urls import include, url

from genesishealth.apps.utils.views import generic_dashboard
from genesishealth.apps.accounts.views import patients as patient_views


id_urlpatterns = [
    url(r'^notes/$',
        patient_views.notes,
        name='manage-patients-notes'),
    url(r'^notes/new/$',
        patient_views.update_note,
        name='manage-patients-notes-create'),
    url(r'^notes/(?P<note_id>\d+?)/$',
        patient_views.update_note,
        name='manage-patients-notes-update'),
    url(r'^records/$',
        patient_views.records,
        name='manage-patients-records'),
    url(r'^detail/$',
        patient_views.detail,
        name='manage-patients-detail'),
    url(r'^communications/$',
        patient_views.communications,
        name='patient-communications'),
    url(r'^communications/new/$',
        patient_views.add_communication,
        name='new-communication'),
    url(r'^communications/(?P<communication_id>\d+)/$',
        patient_views.edit_communication,
        name='edit-communication'),
    url(r'^communications/(?P<communication_id>\d+)/pdf/$',
        patient_views.communication_pdf,
        name='communication-report-pdf'),
    url(r'^communications/(?P<communication_id>\d+)/print/$',
        patient_views.communication_pdf_html,
        name='communication-report-pdf-html'),
    url(r'^orders/$',
        patient_views.orders,
        name='patient-orders'),
]

urlpatterns = [
    url(r'^$',
        patient_views.main,
        name='manage-patients'),
    url(r'^assigned/$',
        patient_views.main,
        {'show_assigned': True},
        name='manage-patients-assigned'),
    url(r'^new/$',
        patient_views.add,
        name='manage-patients-create'),
    url(r'^(?P<patient_id>\d+?)/$',
        patient_views.edit,
        name='manage-patients-edit'),
    url(r'^(?P<patient_id>\d+?)/activate/$',
        patient_views.activate_patient,
        name='manage-patients-activate'),
    url(r'^edit/thanks/$',
        generic_dashboard,
        {'title': 'Edit Patient',
         'content': 'The patient has been updated.'},
        name='manage-patients-edit-thanks'),
    url(r'^batch/assign/$',
        patient_views.batch_assign,
        name='manage-patients-batch-assign'),
    url(r'^batch/delete/$',
        patient_views.batch_delete,
        name='manage-patients-batch-delete'),
    url(r'^batch/unassign/$',
        patient_views.batch_unassign,
        name='manage-patients-batch-unassign'),
    url(r'^batch/assign_to_partner/$',
        patient_views.batch_assign_to_partner,
        name='manage-patients-batch-assign-api-partner'),
    url(r'^batch/unassign_from_partner/$',
        patient_views.batch_unassign_from_partner,
        name='manage-patients-batch-unassign-api-partner'),
    url(r'^batch/migrate/$',
        patient_views.batch_migrate_to_api_partner,
        name='manage-patients-migrate-patient-readings'),
    url(r'^batch/recover_readings/$',
        patient_views.batch_recover_readings,
        name='manage-patients-recover-readings'),
    url(r'^batch/watchlist/$',
        patient_views.batch_add_to_watch_list,
        name='batch-add-to-watch-list'),
    url(r'^batch/watchlist/remove/$',
        patient_views.batch_remove_from_watch_list,
        name='batch-remove-from-watch-list'),
    url(r'^batch/export/$',
        patient_views.batch_csv_export,
        name='batch-csv-export'),
    url(r'^batch/activate/$',
        patient_views.batch_activate_patient,
        name='batch-activate-patients'),
    url(r'^batch/deactivate/$',
        patient_views.batch_deactivate_patient,
        name='batch-deactivate-patients'),
    url(r'^import/$',
        patient_views.import_csv,
        name='manage-patients-import'),
    url(r'^watchlist/$',
        patient_views.watch_list,
        name='watch-list'),
    url(r'^(?P<patient_id>\d+?)/',
        include(id_urlpatterns)),
    url(r'^full_call_log_report/$',
        patient_views.call_log_report,
        name='full-call-log-report')
]
