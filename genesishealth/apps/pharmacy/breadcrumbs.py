from django.urls import reverse

from genesishealth.apps.utils.breadcrumbs import Breadcrumb


def get_rx_partner_breadcrumbs(rx_partner, requester, include_detail=True):
    breadcrumbs = [
        Breadcrumb('Pharmacy Partners',
                   reverse('pharmacy:index'))]
    if include_detail:
        breadcrumbs.append(
            Breadcrumb(
                'Pharmacy Partner: {0}'.format(rx_partner),
                reverse('pharmacy:details', args=[rx_partner.id])))
    return breadcrumbs
