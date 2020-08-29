from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.staticfiles.views import serve
from django.urls import re_path
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView


admin.autodiscover()


urlpatterns = [
    url(r'^readings/',
        include(
            ('genesishealth.apps.readings.urls',
             'genesishealth.apps.readings'),
            namespace='readings')),
    url(r'^accounts/',
        include(
            ('genesishealth.apps.accounts.urls',
             'genesishealth.apps.accounts'),
            namespace='accounts')),
    url(r'^api/mobile/',
        include(
            ('genesishealth.apps.mobile.urls',
             'genesishealth.apps.mobile'),
            namespace='mobile')),
    url(r'^api/',
        include(
            ('genesishealth.apps.healthsplash.urls',
             'genesishealth.apps.healthsplash'),
            namespace='healthsplash')),
    url(r'^dashboard/',
        include(
            ('genesishealth.apps.dashboard.urls',
             'genesishealth.apps.dashboard'),
            namespace='dashboard')),
    url(r'^devices/',
        include(
            ('genesishealth.apps.gdrives.urls',
             'genesishealth.apps.gdrives'),
            namespace='gdrives')),
    url(r'^health_information/',
        include(
            ('genesishealth.apps.health_information.urls',
             'genesishealth.apps.health_information'),
            namespace='health_information')),
    url(r'^reports/',
        include(
            ('genesishealth.apps.reports.urls',
             'genesishealth.apps.reports'),
            namespace='reports')),
    url(r'^contact/',
        include(
            ('genesishealth.apps.contact.urls',
             'genesishealth.apps.contact'),
            namespace='contact')),
    url(r'^logs/',
        include(
            ('genesishealth.apps.logs.urls',
             'genesishealth.apps.logs'),
            namespace='logs')),
    url(r'^alerts/',
        include(
            ('genesishealth.apps.alerts.urls',
             'genesishealth.apps.alerts'),
            namespace='alerts')),
    url(r'^products/',
        include(
            ('genesishealth.apps.products.urls',
             'genesishealth.apps.products'),
            namespace='products')),
    url(r'^tutorial/',
        TemplateView.as_view(
            template_name='tutorial.html'),
        name='tutorial'),
    url(r'^support/',
        TemplateView.as_view(
            template_name='support.html'),
        name='support'),
    url(r'^monitoring/',
        include(
            ('genesishealth.apps.monitoring.urls',
             'genesishealth.apps.monitoring'),
            namespace='monitoring')),
    url(r'^orders/',
        include(
            ('genesishealth.apps.orders.urls',
             'genesishealth.apps.orders'),
            namespace='orders')),
    url(r'^pharmacy/',
        include(
            ('genesishealth.apps.pharmacy.urls',
             'genesishealth.apps.pharmacy'),
            namespace='pharmacy')),
    url(r'^epcapi/',
        include(
            ('genesishealth.apps.epc.urls',
             'genesishealth.apps.epc'),
            namespace='epc')),
    url(r'^nursing/',
        include(
            ('genesishealth.apps.nursing.urls',
             'genesishealth.apps.nursing'),
            namespace='nursing')),
    url(r'^ghtadmin/',
        include(
            ('genesishealth.apps.ghtadmin.urls',
             'genesishealth.apps.ghtadmin'),
            namespace='ghtadmin')),
    url(r'^text_messaging/',
        include(
            ('genesishealth.apps.text_messaging.urls',
             'genesishealth.apps.text_messaging'),
            namespace='text_messaging')),
url(r'^work_queue/',
        include(
            ('genesishealth.apps.work_queue.urls',
             'genesishealth.apps.work_queue'),
            namespace='work_queue')),
    url(r'^admin/', admin.site.urls),
    url(r'^$',
        RedirectView.as_view(url='/dashboard/'),
        name='main-home'),
]

if settings.DEBUG_STATIC_FILES:
    urlpatterns += [re_path(r'^devstatic/(?P<path>.*)$', serve)]
