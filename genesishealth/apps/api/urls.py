from django.conf.urls import url

from genesishealth.apps.api import views


urlpatterns = [
    url(r'^wellness_doc/(?P<pk>\d+)/$',
        views.wellness_doc,
        name="wellness_doc"),
]
