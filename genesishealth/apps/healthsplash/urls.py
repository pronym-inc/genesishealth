from django.conf.urls import url

from genesishealth.apps.healthsplash.api.blood_glucose_graph import BloodGlucoseGraphDetailApiView
from genesishealth.apps.healthsplash.api.get_blood_glucose_stat import GetBloodGlucoseStatApiView
from genesishealth.apps.healthsplash.api.get_token import GenesisGetTokenApiView

urlpatterns = [
    url(r'^get_token/$', GenesisGetTokenApiView.as_view(), name="get_token"),
    url(
        r'^healthsplash/patient/blood_glucose/$',
        GetBloodGlucoseStatApiView.as_view(),
        name="retrieve_blood_glucose"
    ),
    url(
        r'^healthsplash/graph/(?P<id>\d+)/$',
        BloodGlucoseGraphDetailApiView.as_view(),
        name="blood-glucose-graph"
    )
]
