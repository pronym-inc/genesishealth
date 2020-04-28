from django.urls import reverse

from genesishealth.apps.utils.breadcrumbs import Breadcrumb


def get_group_breadcrumbs(group, requester, include_detail=True):
    breadcrumbs = [
        Breadcrumb('Business Partners',
                   reverse('accounts:manage-groups'))
    ]
    if include_detail:
        breadcrumbs.append(
            Breadcrumb(
                'Business Partner: {0}'.format(group.name),
                reverse('accounts:manage-groups-detail',
                        args=[group.pk])))
    return breadcrumbs
