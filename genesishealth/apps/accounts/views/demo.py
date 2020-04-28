from django.http import HttpResponse
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.urls import reverse

from genesishealth.apps.accounts.forms.demo import DemoPatientForm
from genesishealth.apps.accounts.models import GenesisGroup
from genesishealth.apps.accounts.views.base import GroupTableView
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.class_views import (
    AttributeTableColumn, ActionTableColumn,
    ActionItem, GenesisTableLink, GenesisTableLinkAttrArg,
    GenesisAboveTableDropdown, GenesisAboveTableButton,
    GenesisDropdownOption)
from genesishealth.apps.utils.request import admin_user
from genesishealth.apps.utils.views import (
    generic_form, generic_delete_form)


class DemoProfileView(GroupTableView):
    def create_columns(self):
        group = self.get_group()
        if group:
            url_args = [group.id]
            edit_patient_link = 'accounts:manage-groups-demo-edit'
        else:
            url_args = []
            edit_patient_link = 'accounts:manage-demo-edit'
        return [
            AttributeTableColumn('Name', 'get_reversed_name'),
            AttributeTableColumn(
                'MEID', 'patient_profile.get_device.meid'),
            AttributeTableColumn(
                'Last Reading',
                'patient_profile.get_last_reading_date',
                searchable=False),
            AttributeTableColumn(
                'Device Assigned Date',
                'patient_profile.get_device_assigned_date',
                searchable=False),
            AttributeTableColumn(
                'Groups',
                'patient_profile.group_list',
                sortable=False),
            ActionTableColumn(
                'Actions',
                actions=[
                    ActionItem(
                        'Edit Patient',
                        GenesisTableLink(
                            edit_patient_link,
                            url_args=url_args + [
                                GenesisTableLinkAttrArg('pk')]
                        )
                    ),
                    ActionItem(
                        'View Device',
                        GenesisTableLink(
                            'gdrives:edit',
                            url_args=[GenesisTableLinkAttrArg(
                                'patient_profile.get_device.id')],
                        ),
                        condition='patient_profile.get_device'
                    ),
                    ActionItem(
                        'Manage Login',
                        GenesisTableLink(
                            'accounts:manage-login',
                            url_args=[GenesisTableLinkAttrArg('pk')]
                        )
                    ),
                    ActionItem(
                        'View Reports',
                        GenesisTableLink(
                            'reports:patient-index',
                            url_args=[GenesisTableLinkAttrArg('pk')]
                        )
                    )
                ]
            )
        ]

    def get_above_table_items(self):
        group = self.get_group()
        if group:
            add_link = reverse(
                'accounts:manage-groups-demo-create', args=[group.id])
            del_link = reverse(
                'accounts:manage-groups-demo-batch-delete', args=[group.id])
            return [
                GenesisAboveTableButton('Add Demo Patient', add_link),
                GenesisAboveTableDropdown(
                    [GenesisDropdownOption('Delete', del_link)]
                )
            ]
        return []

    def get_breadcrumbs(self):
        group = self.get_group()
        return [
            Breadcrumb('Business Partners',
                       reverse('accounts:manage-groups')),
            Breadcrumb(
                'Business Partner: {0}'.format(group.name),
                reverse('accounts:manage-groups-detail',
                        args=[group.pk]))
        ]

    def get_page_title(self):
        group = self.get_group()
        if group:
            return 'Manage Demo Patients for {}'.format(group)
        return 'Manage Demo Patients'

    def get_prefetch_fields(self):
        return (
            'patient_profile', 'patient_profile__group',
            'patient_profile__last_reading'
        )

    def get_queryset(self):
        group = self.get_group()
        if group:
            qs = group.get_patients()
        else:
            qs = User.objects.filter(patient_profile__isnull=True)
        return qs.filter(patient_profile__demo_patient=True)


test = user_passes_test(admin_user)
main = test(DemoProfileView.as_view())


@user_passes_test(admin_user)
def edit(request, patient_id, group_id=None):
    try:
        if group_id:
            group = GenesisGroup.objects.get(pk=group_id)
            patient = group.get_patients().filter(
                patient_profile__demo_patient=True).get(
                pk=patient_id)
        else:
            patient = User.objects.filter(
                patient_profile__demo_patient=True).get(
                pk=patient_id)
            group = patient.patient_profile.get_group()
    except (GenesisGroup.DoesNotExist, User.DoesNotExist) as e:
        return HttpResponse(repr(e), status=500)

    form_kwargs = {'instance': patient, 'initial_group': group}

    breadcrumbs = [
        Breadcrumb('Business Partners',
                   reverse('accounts:manage-groups')),
        Breadcrumb(
            'Business Partner: {0}'.format(group.name),
            reverse('accounts:manage-groups-detail',
                    args=[group.pk])),
        Breadcrumb(
            'Demo Patients'.format(group.name),
            reverse('accounts:manage-groups-demo',
                    args=[group.pk])),
        Breadcrumb('Patient: {0}'.format(
                   patient.get_reversed_name()),
                   reverse('accounts:manage-patients-detail',
                           args=[patient.pk]))
    ]

    return generic_form(
        request,
        form_class=DemoPatientForm,
        page_title='Edit %s' % patient,
        system_message="The patient has been updated.",
        breadcrumbs=breadcrumbs,
        form_kwargs=form_kwargs)


@user_passes_test(admin_user)
def create(request, group_id):
    try:
        group = GenesisGroup.objects.get(pk=group_id)
    except GenesisGroup.DoesNotExist:
        return HttpResponse(status=500)

    breadcrumbs = [
        Breadcrumb('Business Partners',
                   reverse('accounts:manage-groups')),
        Breadcrumb(
            'Business Partner: {0}'.format(group.name),
            reverse('accounts:manage-groups-detail',
                    args=[group.pk])),
        Breadcrumb(
            'Demo Patients'.format(group.name),
            reverse('accounts:manage-groups-demo',
                    args=[group.pk]))
    ]

    return generic_form(
        request,
        form_class=DemoPatientForm,
        page_title='Create Demo Patient for %s' % group,
        system_message="The patient has been created.",
        breadcrumbs=breadcrumbs,
        form_kwargs={'initial_group': group})


@user_passes_test(admin_user)
def batch_delete(request, group_id):
    try:
        group = GenesisGroup.objects.get(pk=group_id)
    except GenesisGroup.DoesNotExist:
        return HttpResponse(status=500)

    return generic_delete_form(
        request,
        system_message='The selected demo patients have been deleted.',
        page_title='Delete demo patients',
        batch_queryset=group.get_patients().filter(
            patient_profile__demo_patient=True),
        batch=True,
    )
