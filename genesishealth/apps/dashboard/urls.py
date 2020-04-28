from django.conf.urls import url

from genesishealth.apps.dashboard import views

urlpatterns = [
    url(r'^$',
        views.index,
        name='index'),
    url(r'^home/$',
        views.home,
        name='home'),
    url(r'^public/$',
        views.public,
        name='public')
]
