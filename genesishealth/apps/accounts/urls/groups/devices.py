from django.conf.urls import url

from genesishealth.apps.gdrives import views


urlpatterns = [
    url(r'^$',
        views.index,
        name='manage-groups-devices'),
    url(r'^import$',
        views.import_devices,
        name='manage-groups-devices-import'),
    url(r'^import_csv/$',
        views.import_csv,
        name='manage-groups-devices-import-csv'),
    url(r'^new/$',
        views.new,
        name='manage-groups-devices-create'),
]
