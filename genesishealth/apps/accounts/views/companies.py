from typing import Dict, Any, List

from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.http import HttpResponseNotFound

from genesishealth.apps.accounts.models import GenesisGroup, Company
from genesishealth.apps.accounts.forms.companies import (
    CompanyForm, ImportCompaniesForm)
from genesishealth.apps.accounts.views.base import GroupTableView
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.class_views import (
    AttributeTableColumn, ActionTableColumn,
    ActionItem, GenesisTableLink, GenesisTableLinkAttrArg,
    GenesisAboveTableDropdown, GenesisAboveTableButton,
    GenesisDropdownOption, GenesisFormView)
from genesishealth.apps.utils.forms import GenesisModelForm
from genesishealth.apps.utils.request import check_user_type
from genesishealth.apps.utils.views import generic_form, generic_delete_form


class CompanyTableView(GroupTableView):
    def create_columns(self):
        group = self.get_group()
        if self.request.user.is_admin():
            edit_url_name = 'accounts:manage-groups-companies-edit'
            url_args = [group.id]
        else:
            edit_url_name = 'accounts:manage-companies-edit'
            url_args = []
        columns = [
            AttributeTableColumn('Name', 'name', cell_class='main'),
            AttributeTableColumn('Payor/TPA', 'payor.name'),
            AttributeTableColumn('# of Patients', 'patients.count',
                                 searchable=False),
            AttributeTableColumn('Contact Name', 'contact.get_full_name'),
            AttributeTableColumn('Contact #', 'contact.phone', sortable=False),
            AttributeTableColumn('Address', 'contact.get_full_address'),
            AttributeTableColumn('City', 'contact.city'),
            AttributeTableColumn('State', 'contact.state'),
            AttributeTableColumn('Zip', 'contact.zip'),
            ActionTableColumn(
                'Actions',
                actions=[
                    ActionItem(
                        'Edit Company',
                        GenesisTableLink(
                            edit_url_name,
                            url_args=url_args + [
                                GenesisTableLinkAttrArg('pk')]
                        )
                    ),

                ]
            )
        ]
        if self.request.user.is_admin():
            columns.append(ActionTableColumn(
                'Admin',
                actions=[
                    ActionItem(
                        'Admin',
                        GenesisTableLink(
                            'accounts:manage-groups-companies-admin',
                            url_args=url_args + [GenesisTableLinkAttrArg('pk')]
                        )
                    )
                ]
            ))
        return columns

    def get_above_table_items(self):
        group = self.get_group()
        if self.request.user.is_admin():
            add_link_name = 'accounts:manage-groups-companies-create'
            del_link_name = 'accounts:manage-groups-companies-batch-delete'
            import_link_name = 'accounts:manage-groups-companies-import'
            link_args = [group.id]
        else:
            add_link_name = 'accounts:manage-companies-create'
            del_link_name = 'accounts:manage-companies-batch-delete'
            import_link_name = 'accounts:manage-companies-import'
            link_args = []
        add_link = reverse(add_link_name, args=link_args)
        del_link = reverse(del_link_name, args=link_args)
        import_link = reverse(import_link_name, args=link_args)
        return [
            GenesisAboveTableButton('Add Company', add_link),
            GenesisAboveTableButton('Import Companies', import_link),
            GenesisAboveTableDropdown(
                [GenesisDropdownOption('Delete', del_link)]
            )
        ]

    def get_authorized_user_types(self):
        if 'group_id' in self.kwargs:
            return ['admin']
        return ['professional']

    def get_breadcrumbs(self):
        if self.request.user.is_admin():
            group = self.get_group()
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
        page_title = 'Manage Groups/Employers for {}'.format(group)
        return page_title

    def get_queryset(self):
        group = self.get_group()
        return group.companies.all()


access_check = user_passes_test(
    lambda u: check_user_type(u, ['Admin', 'Professional']))


main = access_check(CompanyTableView.as_view())


@login_required
@user_passes_test(lambda u: check_user_type(u, ['Admin', 'Professional']))
def add(request, group_id=None):
    if group_id:
        if not request.user.is_admin():
            return HttpResponseNotFound()
        group = GenesisGroup.objects.get(pk=group_id)
        page_title = 'Add Group/Employer for %s' % group
    else:
        if not request.user.is_professional():
            return HttpResponseNotFound()
        group = request.user.professional_profile.parent_group
        page_title = 'Add Group/Employer'

    if request.user.is_admin():
        breadcrumbs = [
            Breadcrumb('Business Partners',
                       reverse('accounts:manage-groups')),
            Breadcrumb(
                'Business Partner: {0}'.format(group.name),
                reverse('accounts:manage-groups-detail',
                        args=[group.pk])),
            Breadcrumb(
                'Companies',
                reverse('accounts:manage-groups-companies',
                        args=[group.pk]))
        ]
    else:
        breadcrumbs = []

    return generic_form(
        request,
        form_class=CompanyForm,
        page_title=page_title,
        system_message="The group/employer has been created.",
        breadcrumbs=breadcrumbs,
        form_kwargs={'initial_group': group})


@user_passes_test(lambda u: check_user_type(u, ['Admin', 'Professional']))
def import_csv(request, group_id=None):
    if group_id:
        if not request.user.is_admin():
            return HttpResponseNotFound()
        group = GenesisGroup.objects.get(pk=group_id)
    else:
        if not request.user.is_professional():
            return HttpResponseNotFound()
        group = request.user.professional_profile.parent_group

    if request.user.is_admin():
        breadcrumbs = [
            Breadcrumb('Business Partners',
                       reverse('accounts:manage-groups')),
            Breadcrumb(
                'Business Partner: {0}'.format(group.name),
                reverse('accounts:manage-groups-detail',
                        args=[group.pk])),
            Breadcrumb(
                'Companies',
                reverse('accounts:manage-groups-companies',
                        args=[group.pk]))
        ]
    else:
        breadcrumbs = []

    return generic_form(
        request,
        form_class=ImportCompaniesForm,
        form_kwargs={'initial_group': group},
        page_title='Import Companies for %s' % group,
        breadcrumbs=breadcrumbs,
        system_message='The companies have been imported')


@user_passes_test(lambda u: check_user_type(u, ['Admin', 'Professional']))
def batch_delete(request, group_id=None):
    if group_id:
        if not request.user.is_admin():  # pragma: no cover
            return HttpResponseNotFound()
        group = GenesisGroup.objects.get(pk=group_id)
    else:
        if not request.user.is_professional():  # pragma: no cover
            return HttpResponseNotFound()
        group = request.user.professional_profile.parent_group

    return generic_delete_form(
        request,
        system_message='The selected companies have been deleted.',
        batch_queryset=group.companies.all(),
        batch=True,
    )


@user_passes_test(lambda u: check_user_type(u, ['Admin', 'Professional']))
def edit(request, company_id, group_id=None):
    if group_id:
        if not request.user.is_admin():
            return HttpResponseNotFound()
        group = GenesisGroup.objects.get(pk=group_id)
    else:
        if not request.user.is_professional():
            return HttpResponseNotFound()
        group = request.user.professional_profile.parent_group
    company = group.companies.get(pk=company_id)

    if request.user.is_admin():
        breadcrumbs = [
            Breadcrumb('Business Partners',
                       reverse('accounts:manage-groups')),
            Breadcrumb(
                'Business Partner: {0}'.format(group.name),
                reverse('accounts:manage-groups-detail',
                        args=[group.pk])),
            Breadcrumb(
                'Companies',
                reverse('accounts:manage-groups-companies',
                        args=[group.pk]))
        ]
    else:
        breadcrumbs = []

    return generic_form(
        request,
        form_class=CompanyForm,
        page_title='Edit Group/Employer',
        system_message="The group/employer has been updated.",
        breadcrumbs=breadcrumbs,
        form_kwargs={'initial_group': group, 'instance': company})


class CompanyAdminForm(GenesisModelForm):
    class Meta:
        model = Company
        fields = [
            'reading_too_high_interval',
            'reading_too_high_threshold',
            'reading_too_high_limit',
            'reading_too_low_interval',
            'reading_too_low_threshold',
            'reading_too_low_limit',
            'not_enough_recent_readings_interval',
            'not_enough_recent_readings_minimum'
        ]


class CompanyAdminView(GenesisFormView):
    form_class = CompanyAdminForm
    page_title = "Administrate Company"
    go_back_until = ['accounts:manage-groups-companies']
    success_message = "The company has been updated."

    def _get_breadcrumbs(self) -> List[Breadcrumb]:
        group = self.get_group()
        return [
            Breadcrumb('Business Partners',
                       reverse('accounts:manage-groups')),
            Breadcrumb(
                'Business Partner: {0}'.format(group.name),
                reverse('accounts:manage-groups-detail',
                        args=[group.pk])),
            Breadcrumb(
                'Companies',
                reverse('accounts:manage-groups-companies',
                        args=[group.pk])),
        ]

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.get_company()
        return kwargs

    def get_company(self) -> Company:
        return Company.objects.get(pk=self.kwargs['company_id'])

    def get_group(self) -> GenesisGroup:
        return self.get_company().group


company_admin = user_passes_test(
    lambda u: check_user_type(u, ['Admin'])
)(CompanyAdminView.as_view())
