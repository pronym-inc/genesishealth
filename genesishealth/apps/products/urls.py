from django.conf.urls import url

from genesishealth.apps.products import views


urlpatterns = [
    url(r'^$',
        views.index,
        name="index"),
    url(r'^new/$',
        views.add_product_type,
        name="add"),
    url(r'^edit/(?P<product_type_id>\d+)/$',
        views.edit_product_type,
        name="edit"),
    url(r'^import/$',
        views.import_product_types,
        name="import")
]
