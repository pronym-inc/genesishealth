from django.conf.urls import url

from genesishealth.apps.notes.views.add_note import add_patient_note
from genesishealth.apps.notes.views.notes import patient_notes


urlpatterns = [
    url(
        r'(?P<patient_id>\d+)/$',
        patient_notes,
        name="patient-notes"
    ),
    url(
        r'(?P<patient_id>\d+)/add/$',
        add_patient_note,
        name="patient-notes-add"
    )
]
