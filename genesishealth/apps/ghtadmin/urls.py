from django.conf.urls import url

from genesishealth.apps.ghtadmin.views import dashboard


urlpatterns = [
    url(r'^$',
        dashboard.main,
        name="dashboard")]
