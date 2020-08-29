from django.conf.urls import url

from genesishealth.apps.healthsplash.api.get_token import GenesisGetTokenApiView
from genesishealth.apps.mobile.api.me import MeApiView

urlpatterns = [
    url(r'^get_token/$', GenesisGetTokenApiView.as_view(), name="get_token"),
    url(
        r'^me/$',
        MeApiView.as_view(),
        name="me"
    )
]
