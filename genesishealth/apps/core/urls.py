from django.conf.urls import url
from django.views.generic import TemplateView


app_name = 'core'
urlpatterns = [
    url(r'^$',
        TemplateView.as_view(template_name="core/index.html"),
        name='index')
]