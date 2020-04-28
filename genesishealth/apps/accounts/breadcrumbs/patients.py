from django.urls import reverse

from genesishealth.apps.utils.breadcrumbs import Breadcrumb

from .groups import get_group_breadcrumbs


def get_communication_breadcrumbs(communication, requester,
                                  include_detail=True):
    patient = communication.patient
    breadcrumbs = get_patient_breadcrumbs(patient, requester)
    breadcrumbs.append(
        Breadcrumb('Communications',
                   reverse('accounts:patient-communications',
                           args=[patient.pk]))
    )
    return breadcrumbs


def get_patient_breadcrumbs(patient, requester, include_detail=True):
    if requester.is_admin():
        group = patient.patient_profile.get_group()
        if group:
            breadcrumbs = get_group_breadcrumbs(group, requester)
            breadcrumbs.append(
                Breadcrumb(
                    'Patients'.format(group.name),
                    reverse('accounts:manage-groups-patients',
                            args=[group.pk])))
        else:
            breadcrumbs = [
                Breadcrumb('Users',
                           reverse('accounts:manage-users'))
            ]
    else:
        breadcrumbs = [
            Breadcrumb(
                'Patients',
                reverse('accounts:manage-patients'))
        ]
    if include_detail:
        breadcrumbs.append(
            Breadcrumb('Patient: {0}'.format(
                       patient.get_reversed_name()),
                       reverse('accounts:manage-patients-detail',
                               args=[patient.pk])))
    return breadcrumbs
