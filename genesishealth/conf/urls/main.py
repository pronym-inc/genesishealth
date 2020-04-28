from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.views import serve
from django.urls import include, path, re_path


admin.autodiscover()


urlpatterns = [
    path(r'admin/', admin.site.urls),
    path('', include('genesishealth.apps.core.urls', namespace='core')),
]

if settings.DEBUG_STATIC_FILES:
    urlpatterns += [re_path(r'^devstatic/(?P<path>.*)$', serve)]