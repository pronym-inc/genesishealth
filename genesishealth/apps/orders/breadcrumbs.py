from django.urls import reverse

from genesishealth.apps.utils.breadcrumbs import Breadcrumb


def get_order_breadcrumbs(order, requester, include_detail=True):
    breadcrumbs = [Breadcrumb('Orders', reverse('orders:index'))]
    if include_detail:
        breadcrumbs.append(
            Breadcrumb('Order {0} for {1}'.format(
                order.id, order.get_recipient_name()),
                reverse('orders:details', args=[order.pk])))
    return breadcrumbs
