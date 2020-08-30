from django.conf.urls import url

from genesishealth.apps.healthsplash.api.get_token import GenesisGetTokenApiView
from genesishealth.apps.mobile.api.blood_pressure_reading_collection import BloodPressureReadingCollectionApiView
from genesishealth.apps.mobile.api.blood_pressure_reading_detail import BloodPressureReadingDetailApiView
from genesishealth.apps.mobile.api.me import MeApiView
from genesishealth.apps.mobile.api.update_expo_push_token import UpdateExpoPushTokenApiView

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
    ),
    url(
        r'update_expo_push_token/$',
        UpdateExpoPushTokenApiView.as_view(),
        name="update-expo-push-token"
    )
]
