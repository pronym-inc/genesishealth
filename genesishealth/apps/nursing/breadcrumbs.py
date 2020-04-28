from django.urls import reverse

from genesishealth.apps.utils.breadcrumbs import Breadcrumb


def get_nursing_group_breadcrumbs(
        nursing_group, requester, include_detail=True):
    breadcrumbs = [
        Breadcrumb('Nursing Group',
                   reverse('nursing:index'))]
    if include_detail:
        breadcrumbs.append(
            Breadcrumb(
                'Nursing Group: {0}'.format(nursing_group),
                reverse('nursing:details', args=[nursing_group.id])))
    return breadcrumbs
