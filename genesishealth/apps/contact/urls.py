from django.conf.urls import url

from genesishealth.apps.contact import views

urlpatterns = [
    url(r'^$',
        views.contact,
        name='contact-main'),
]
