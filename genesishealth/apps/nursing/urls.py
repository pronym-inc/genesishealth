from django.conf.urls import url

from .views.nursing_group.create import main as create
from .views.nursing_group.details import main as details
from .views.nursing_group.edit import main as edit
from .views.nursing_group.index import main as index


urlpatterns = [
    url(r'^$',
        index,
        name="index"),
    url(r'^create/$',
        create,
        name="create"),
    url(r'^(?P<nursing_group_id>\d+)/$',
        details,
        name="details"),
    url(r'^(?P<nursing_group_id>\d+)/edit/$',
        edit,
        name="edit")
]
