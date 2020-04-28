from django.conf.urls import url

from .views.bulk_order import create as create_bulk_order, partner as partner_bulk_order
from .views.partner import create, details, edit, fulfill_orders, import_orders, index


urlpatterns = [
    url(r'^$',
        index.main,
        name="index"),
    url(r'^create/$',
        create.main,
        name="create"),
    url(r'^(?P<rx_partner_id>\d+)/$',
        details.main,
        name="details"),
    url(r'^(?P<rx_partner_id>\d+)/edit/$',
        edit.main,
        name="edit"),
    url(r'^(?P<rx_partner_id>\d+)/create_bulk_order/$',
        create_bulk_order.main,
        name="create-bulk-order"),
    url(r'^(?P<rx_partner_id>\d+)/import_orders/$',
        import_orders.main,
        name="import-orders"),
    url(r'^(?P<rx_partner_id>\d+)/fulfill_orders/$',
        fulfill_orders.main,
        name="fulfill-orders"),
    url(r'^(?P<rx_partner_id>\d+)/orders/$',
        partner_bulk_order.main,
        name="partner-bulk-orders"),
]
