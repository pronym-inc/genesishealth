from django.conf.urls import url

from genesishealth.apps.healthsplash.api.get_token import GenesisGetTokenApiView
from genesishealth.apps.mobile.api.blood_pressure_reading.collection import BloodPressureReadingCollectionApiView
from genesishealth.apps.mobile.api.blood_pressure_reading.detail import BloodPressureReadingDetailApiView
from genesishealth.apps.mobile.api.glucose_reading.collection import GlucoseReadingCollectionApiView
from genesishealth.apps.mobile.api.me import MeApiView
from genesishealth.apps.mobile.api.notifications.collection import MobileNotificationCollectionApiView
from genesishealth.apps.mobile.api.notifications.detail import MobileNotificationDetailApiView
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
        r'glucose_reading/$',
        GlucoseReadingCollectionApiView.as_view(),
        name="glucose-reading-collection"
    ),
    url(
        r'update_expo_push_token/$',
        UpdateExpoPushTokenApiView.as_view(),
        name="update-expo-push-token"
    ),
    url(
        r'notification/$',
        MobileNotificationCollectionApiView.as_view(),
        name="mobile-notification-collection"
    ),
    url(
        r'notification/(?P<id>\d+)/$',
        MobileNotificationDetailApiView.as_view(),
        name="mobile-notification-detail"
    )
]
