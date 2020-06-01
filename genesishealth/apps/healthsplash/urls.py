from django.conf.urls import url
from pronym_api.api.get_token import GetTokenApiView

from genesishealth.apps.healthsplash.api.get_blood_glucose_stat import GetBloodGlucoseStatApiView

urlpatterns = [
    url(r'^get_token/$', GetTokenApiView.as_view(), name="get_token"),
    url(
        r'^healthsplash/patient/blood_glucose',
        GetBloodGlucoseStatApiView.as_view(),
        name="retrieve_blood_glucose"
    )
]
