from django.urls import reverse

from genesishealth.apps.accounts.breadcrumbs.patients import (
    get_patient_breadcrumbs)
from genesishealth.apps.utils.breadcrumbs import Breadcrumb


def get_device_breadcrumbs(device, requester, include_detail=True):
    patient = device.get_patient()
    if patient:
        breadcrumbs = get_patient_breadcrumbs(patient, requester)
        breadcrumbs.append(
            Breadcrumb(
                'Devices',
                reverse('gdrives:patient-details', args=[patient.pk])
            )
        )
    else:
        breadcrumbs = []
    if include_detail:
        breadcrumbs.append(
            Breadcrumb('Device: {0}'.format(device.meid),
                       reverse('gdrives:detail', args=[device.pk])))
    return breadcrumbs
