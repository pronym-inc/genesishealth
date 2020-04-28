from django.conf.urls import url

from genesishealth.apps.health_information import views

urlpatterns = []

urlpatterns = [
    url(r'(?P<patient_id>\d+)/$',
        views.edit,
        name='edit-health-information-for-patient'),
    url(r'(?P<patient_id>\d+)/targets/$',
        views.edit_targets,
        name='edit-health-targets'),
    url(r'$',
        views.edit,
        name='edit-health-information'),
]
