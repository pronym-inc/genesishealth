from django.conf.urls import url

from genesishealth.apps.healthsplash.api.get_token import GenesisGetTokenApiView
from genesishealth.apps.mobile.api.blood_pressure_reading_collection import BloodPressureReadingCollectionApiView
from genesishealth.apps.mobile.api.blood_pressure_reading_detail import BloodPressureReadingDetailApiView
from genesishealth.apps.mobile.api.me import MeApiView

urlpatterns = [
    url(r'^get_token/$', GenesisGetTokenApiView.as_view(), name="get_token"),
    url(
        r'^me/$',
        MeApiView.as_view(),
        name="me"
    ),
    url(
        r'blood_pressure_reading/$',
        BloodPressureReadingCollectionApiView.as_view(),
        name="blood-pressure-reading-collection"
    ),
    url(
        r'blood_pressure_reading/(?P<id>\d+)/$',
        BloodPressureReadingDetailApiView.as_view(),
        name="blood-pressure-reading-detail"
    )
]
