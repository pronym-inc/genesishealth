from datetime import timedelta

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.urls import reverse
from django.http import Http404
from django.utils.timezone import now

from genesishealth.apps.accounts.models import (
    ProfessionalProfile, GenesisGroup, PatientProfile)
from genesishealth.apps.accounts.forms.professionals import (
    ProfessionalForm, ImportProfessionalForm,
    BatchCaregiverAssignForm, BatchCaregiverUnassignForm,
    ProfessionalNoncompliantReportForm, ProfessionalTargetRangeReportForm)
from genesishealth.apps.accounts.views.base import GroupTableView
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.class_views import (
    AttributeTableColumn, ActionTableColumn,
    ActionItem, GenesisBaseDetailPane, GenesisDetailView,
    GenesisTableLink, GenesisTableLinkAttrArg,
    GenesisAboveTableDropdown, GenesisAboveTableButton,
    GenesisDropdownOption, GenesisTableView)
from genesishealth.apps.utils.request import (
    admin_user, check_user_type,
    debug_response)
from genesishealth.apps.utils.views import (
    generic_form, generic_delete_form)


class ProfessionalTableView(GroupTableView):
    def create_columns(self):
        if self.request.user.is_admin():
            actions = [ActionItem(
                'Detail',
                GenesisTableLink(
                    'accounts:manage-professionals-detail',
                    url_args=[GenesisTableLinkAttrArg('pk')])
            )]
        else:
            actions = [
                ActionItem(
                    'Edit Professional',
                    GenesisTableLink(
                        'accounts:manage-professionals-edit',
                        url_args=[GenesisTableLinkAttrArg('pk')]
                    )
                ),
                ActionItem(
                    'Manage Patients',
                    GenesisTableLink(
                        'accounts:manage-professionals-patients',
                        url_args=[GenesisTableLinkAttrArg('pk')]
                    )
                )
            ]
        return [
            AttributeTableColumn(
                'Contact Name', 'get_reversed_name', cell_class='main',
                proxy_field='last_name'),
            AttributeTableColumn(
                'Contact #', 'professional_profile.contact.phone',
                sortable=False),
            AttributeTableColumn(
                '# of Patients', 'professional_profile.patients.count'),
            ActionTableColumn('View', actions=actions)
        ]

    def get_above_table_items(self):
        group = self.get_group()
        if group is None:
            return []
        if self.request.user.is_admin():
            add_url = reverse(
                'accounts:manage-groups-professionals-create', args=[group.id])
            delete_url = reverse(
                'accounts:manage-groups-professionals-batch-delete',
                args=[group.id])
            import_url = reverse(
                'accounts:manage-groups-professionals-import', args=[group.id])
        else:
            add_url = reverse('accounts:manage-professionals-create')
            delete_url = reverse('accounts:manage-professionals-batch-delete')
            import_url = reverse('accounts:manage-professionals-import')
        items = [
            GenesisAboveTableButton('Add Professional', add_url),
            GenesisAboveTableButton('Import Professionals', import_url)
        ]
        if self.request.user.is_admin():
            items.append(GenesisAboveTableDropdown(
                [GenesisDropdownOption('Delete', delete_url)]
            ))
        return items

    def get_breadcrumbs(self):
        group = self.get_group()
        if group:
            return [
                Breadcrumb('Business Partners',
                           reverse('accounts:manage-groups')),
                Breadcrumb(
                    'Business Partner: {0}'.format(group.name),
                    reverse('accounts:manage-groups-detail',
                            args=[group.pk]))
            ]
        return []

    def get_page_title(self):
        group = self.get_group()
        if group:
            return 'Manage Professionals for {}'.format(group)
        return 'Manage Professionals'

    def get_queryset(self):
        if self.request.user.is_professional():
            group = self.request.user.professional_profile.parent_group
        else:
            group = self.get_group()

        if group:
            return group.get_professionals()
        assert self.request.user.is_admin()
        return ProfessionalProfile.objects.get_users()


test = user_passes_test(
    lambda u: check_user_type(u, ['Admin', 'Professional']))
main = login_required(test(ProfessionalTableView.as_view()))


class CaregiverPatientTableView(GenesisTableView):
    def create_columns(self):
        return [
            AttributeTableColumn(
                'Last Name', 'last_name', cell_class='main'),
            AttributeTableColumn(
                'First Name', 'first_name', cell_class='main'),
            AttributeTableColumn(
                'Date of Birth', 'patient_profile.date_of_birth'),
            AttributeTableColumn(
                'Insurance Identifier',
                'patient_profile.insurance_identifier'),
            AttributeTableColumn(
                'Payor/TPA', 'patient_profile.company.payor.name'),
            AttributeTableColumn(
                'Group/Employer', 'patient_profile.company.name'),
            AttributeTableColumn(
                'API Partner', 'patient_profile.get_partner_string'),
            AttributeTableColumn(
                'Phone Number', 'patient_profile.contact.phone',
                sortable=False)
        ]

    def get_above_table_items(self):
        prof = self.get_professional()
        if self.should_show_assigned():
            button_name = 'Show Unassigned Patients'
            button_link = reverse(
                'accounts:manage-professionals-patients', args=[prof.id])
            options = [GenesisDropdownOption(
                'Unassign Patients',
                reverse(
                    'accounts:manage-professionals-patients-batch-unassign',
                    args=[prof.id])
            )]
        else:
            button_name = 'Show Assigned Patients'
            button_link = reverse(
                'accounts:manage-professionals-patients-assigned',
                args=[prof.id])
            options = [GenesisDropdownOption(
                'Assign Patients',
                reverse(
                    'accounts:manage-professionals-patients-batch-assign',
                    args=[prof.id])
            )]
        return [
            GenesisAboveTableButton(button_name, button_link),
            GenesisAboveTableDropdown(options)
        ]

    def get_breadcrumbs(self):
        user = self.get_professional()
        group = user.professional_profile.parent_group
        return [
            Breadcrumb('Business Partners',
                       reverse('accounts:manage-groups')),
            Breadcrumb(
                'Business Partner: {0}'.format(group.name),
                reverse('accounts:manage-groups-detail',
                        args=[group.pk])),
            Breadcrumb(
                'Professionals',
                reverse('accounts:manage-groups-professionals',
                        args=[group.pk])),
            Breadcrumb(
                'Professional: {0}'.format(user.get_reversed_name()),
                reverse('accounts:manage-professionals-detail',
                        args=[user.pk])
            )
        ]

    def get_page_title(self):
        prof = self.get_professional()
        if self.should_show_assigned():
            return 'Manage Assigned Patients for {}'.format(
                prof.get_reversed_name())
        return 'Manage Unassigned Patients for {}'.format(
            prof.get_reversed_name())

    def get_professional(self):
        if not hasattr(self, '_prof'):
            self._prof = None
        if self._prof is None:
            self._prof = User.objects.filter(
                professional_profile__isnull=False).get(
                id=self.kwargs['user_id'])
        return self._prof

    def get_queryset(self):
        prof = self.get_professional()
        qs = User.objects.filter(patient_profile__isnull=False)
        query_kwargs = {
            'patient_profile__professionals': prof.professional_profile,
            'account_status': PatientProfile.ACCOUNT_STATUS_ACTIVE
        }
        if self.should_show_assigned():
            return qs.filter(**query_kwargs)
        return qs.exclude(**query_kwargs)

    def should_show_assigned(self):
        return self.kwargs.get('show_assigned', False)


admin_test = user_passes_test(admin_user)
manage_caregiver_patients = login_required(
    admin_test(CaregiverPatientTableView.as_view()))


@user_passes_test(admin_user)
def manage_caregiver_patients_batch_assign(request, user_id):
    try:
        prof = User.objects.filter(
            professional_profile__isnull=False).get(id=user_id)
    except User.DoesNotExist:
        raise Http404
    return generic_form(
        request,
        form_class=BatchCaregiverAssignForm,
        form_kwargs={'professional': prof},
        page_title='Assign Patients to {}'.format(prof.get_reversed_name()),
        system_message="The patients have been assigned.",
        batch=True,
        only_batch_input=True,
        go_back_until=['manage-professionals-patients'],
        batch_queryset=PatientProfile.objects.get_users()
    )


@user_passes_test(admin_user)
def manage_caregiver_patients_batch_unassign(request, user_id):
    try:
        prof = User.objects.filter(
            professional_profile__isnull=False).get(id=user_id)
    except User.DoesNotExist:
        raise Http404
    return generic_form(
        request,
        form_class=BatchCaregiverUnassignForm,
        form_kwargs={'professional': prof},
        page_title='Unassign Patients from {}'.format(
            prof.get_reversed_name()),
        system_message="The patients have been unassigned.",
        batch=True,
        only_batch_input=True,
        go_back_until=['manage-professionals-patients'],
        batch_queryset=PatientProfile.objects.get_users()
    )


@login_required
@user_passes_test(lambda u: check_user_type(u, ['Admin', 'Professional']))
def add(request, group_id=None):
    try:
        if group_id:
            assert request.user.is_admin()
            group = GenesisGroup.objects.get(pk=group_id)
            thanks_view_name = reverse(
                'accounts:manage-groups-professionals',
                args=[group.id]
            )
        else:
            assert request.user.is_professional()
            group = request.user.professional_profile.parent_group
            thanks_view_name = reverse('accounts:manage-professionals')
    except (GenesisGroup.DoesNotExist, AssertionError) as e:
        return debug_response(e)

    if request.user.is_admin():
        breadcrumbs = [
            Breadcrumb('Business Partners',
                       reverse('accounts:manage-groups')),
            Breadcrumb(
                'Business Partner: {0}'.format(group.name),
                reverse('accounts:manage-groups-detail',
                        args=[group.pk])),
            Breadcrumb(
                'Professionals',
                reverse('accounts:manage-groups-professionals',
                        args=[group.pk]))
        ]
    else:
        breadcrumbs = []

    return generic_form(
        request,
        form_class=ProfessionalForm,
        form_kwargs={'requester': request.user, 'initial_group': group},
        page_title='Add Professional',
        thanks_view_name=thanks_view_name,
        breadcrumbs=breadcrumbs,
        system_message='The professional has been added.'
    )


@user_passes_test(lambda u: check_user_type(u, ['Admin', 'Professional']))
def import_csv(request, group_id=None):
    try:
        if group_id:
            assert request.user.is_admin()
            group = GenesisGroup.objects.get(pk=group_id)
        else:
            assert request.user.is_professional()
            group = request.user.professional_profile.parent_group
    except (AssertionError, GenesisGroup.DoesNotExist) as e:
        return debug_response(e)

    if request.user.is_admin():
        breadcrumbs = [
            Breadcrumb('Business Partners',
                       reverse('accounts:manage-groups')),
            Breadcrumb(
                'Business Partner: {0}'.format(group.name),
                reverse('accounts:manage-groups-detail',
                        args=[group.pk])),
            Breadcrumb(
                'Professionals',
                reverse('accounts:manage-groups-professionals',
                        args=[group.pk]))
        ]
    else:
        breadcrumbs = []

    return generic_form(
        request,
        form_class=ImportProfessionalForm,
        form_kwargs={'requester': request.user, 'initial_group': group},
        page_title='Import Professional',
        breadcrumbs=breadcrumbs,
        system_message='The professionals have been imported')


@login_required
@user_passes_test(lambda u: check_user_type(u, ['Admin', 'Professional']))
def batch_delete(request, group_id=None):
    try:
        if group_id:
            assert request.user.is_admin()
            group = GenesisGroup.objects.get(pk=group_id)
        else:
            assert request.user.is_professional()
            group = request.user.professional_profile.parent_group
    except (GenesisGroup.DoesNotExist, AssertionError) as e:
        return debug_response(e)

    return generic_delete_form(
        request,
        system_message='The selected professionals have been deleted.',
        page_title='Delete professionals',
        batch_queryset=group.get_professionals(),
        batch=True,
    )


@login_required
@user_passes_test(lambda u: check_user_type(u, ['Admin', 'Professional']))
def edit(request, user_id, group_id=None):
    group = None
    user = None
    try:
        if group_id:
            assert request.user.is_admin()
            group = GenesisGroup.objects.get(pk=group_id)
            user = group.get_professionals().get(pk=user_id)
        else:
            if request.user.is_admin():
                user = ProfessionalProfile.objects.get_users().get(pk=user_id)
                group = user.professional_profile.parent_group
            elif request.user.is_professional():
                group = request.user.professional_profile.parent_group
                user = group.get_professionals().get(pk=user_id)
    except (User.DoesNotExist, GenesisGroup.DoesNotExist, AssertionError) as e:
        return debug_response(e)

    if request.user.is_admin():
        breadcrumbs = [
            Breadcrumb('Business Partners',
                       reverse('accounts:manage-groups')),
            Breadcrumb(
                'Business Partner: {0}'.format(group.name),
                reverse('accounts:manage-groups-detail',
                        args=[group.pk])),
            Breadcrumb(
                'Professionals',
                reverse('accounts:manage-groups-professionals',
                        args=[group.pk])),
            Breadcrumb(
                'Professional: {0}'.format(user.get_reversed_name()),
                reverse('accounts:manage-professionals-detail',
                        args=[user.pk])
            )
        ]
    else:
        breadcrumbs = []

    return generic_form(
        request,
        breadcrumbs=breadcrumbs,
        form_class=ProfessionalForm,
        form_kwargs={
            'requester': request.user,
            'initial_group': group,
            'instance': user
        },
        page_title='Edit Professional',
        system_message='The professional has been updated.'
    )


@login_required
@user_passes_test(lambda u: check_user_type(u, ['Professional']))
def professional_noncompliant_report(request):
    return generic_form(
        request,
        form_class=ProfessionalNoncompliantReportForm,
        form_kwargs={'user': request.user},
        page_title='Generate Non-Compliant Report',
        system_message='Your report has been generated.',
        send_download_url=True)


@user_passes_test(lambda u: check_user_type(u, ['Professional']))
def professional_target_range_report(request):
    return generic_form(
        request,
        form_class=ProfessionalTargetRangeReportForm,
        form_kwargs={'user': request.user},
        page_title='Generate Target Range Report',
        system_message='Your report has been generated.',
        send_download_url=True)


class ProfessionalInformationPane(GenesisBaseDetailPane):
    template_name = 'accounts/professionals/detail_panes/information.html'
    pane_title = "Information"


class ProfessionalStatisticsPane(GenesisBaseDetailPane):
    template_name = 'accounts/professionals/detail_panes/statistics.html'
    pane_title = "Shipping Snapshot"


class ProfessionalLoginPane(GenesisBaseDetailPane):
    template_name = 'accounts/professionals/detail_panes/login_activity.html'
    pane_title = "People Snapshot"


class ProfessionalDetailView(GenesisDetailView):
    pane_classes = (
        ProfessionalInformationPane, ProfessionalStatisticsPane,
        ProfessionalLoginPane,)

    def __init__(self, *args, **kwargs):
        self._professional = None
        super(ProfessionalDetailView, self).__init__(*args, **kwargs)

    def get_breadcrumbs(self):
        group = self.get_professional().professional_profile.parent_group
        return [
            Breadcrumb('Business Partners',
                       reverse('accounts:manage-groups')),
            Breadcrumb(
                'Business Partner: {0}'.format(group.name),
                reverse('accounts:manage-groups-detail',
                        args=[group.pk])),
            Breadcrumb(
                'Professionals',
                reverse('accounts:manage-groups-professionals',
                        args=[group.pk]))
        ]

    def get_buttons(self):
        professional = self.get_professional()
        return [
            GenesisAboveTableButton(
                'Password',
                reverse('accounts:manage-login', args=[professional.pk])),
            GenesisAboveTableButton(
                'Account',
                reverse('accounts:manage-professionals-edit',
                        args=[professional.pk])),
            GenesisAboveTableButton(
                'Patients',
                reverse('accounts:manage-professionals-patients',
                        args=[professional.pk])),
        ]

    def get_page_title(self):
        return 'Manage Professional {0}'.format(
            self.get_professional().get_reversed_name())

    def get_professional(self):
        if self._professional is None:
            self._professional = User.objects.filter(
                professional_profile__isnull=False).get(
                pk=self.kwargs['user_id'])
        return self._professional

    def get_pane_context(self):
        professional = self.get_professional()
        return {
            'professional': professional,
            'last_login': professional.professional_profile.get_last_login(),
            'logins_last_six_months': professional.login_records.filter(
                datetime__gt=now() - timedelta(days=182)).count()
        }


test = user_passes_test(admin_user)
detail = test(ProfessionalDetailView.as_view())
