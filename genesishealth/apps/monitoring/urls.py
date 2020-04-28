from django.conf.urls import url

from genesishealth.apps.monitoring import views


urlpatterns = [
    url(r'^$',
        views.dashboard,
        name="dashboard"),
    url(r'^data/web/$',
        views.web_server_data,
        name="web_server_data"),
    url(r'^data/database/$',
        views.database_server_data,
        name="database_server_data"),
    url(r'^data/worker/$',
        views.worker_server_data,
        name="worker_server_data"),
    url(r'^data/reading/$',
        views.reading_server_data,
        name="reading_server_data"),
    url(r'^scalability/$',
        views.scalability,
        name="scalability"),
    url(r'^scalability/new/$',
        views.scalability_new,
        name="scalability-new")
]
