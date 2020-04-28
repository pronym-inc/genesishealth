from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse

from genesishealth.apps.accounts.models import Payor, GenesisGroup
from genesishealth.apps.accounts.forms.payors import (
    PayorForm, ImportPayorsForm)
from genesishealth.apps.accounts.views.base import GroupTableView
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.class_views import (
    AttributeTableColumn, ActionTableColumn,
    ActionItem, GenesisTableLink, GenesisTableLinkAttrArg,
    GenesisAboveTableDropdown, GenesisAboveTableButton,
    GenesisDropdownOption)
from genesishealth.apps.utils.request import check_user_type, debug_response
from genesishealth.apps.utils.views import (
    generic_form, generic_delete_form)


class PayorTableView(GroupTableView):
    def create_columns(self):
        group = self.get_group()
        if group:
            edit_link = 'accounts:manage-groups-payors-edit'
            url_args = [group.pk]
        else:
            edit_link = 'accounts:manage-payors-edit'
            url_args = []

        return [
            AttributeTableColumn('Payor/TPA', 'name', cell_class='main'),
            AttributeTableColumn('# of Patients', 'get_patients.count'),
            AttributeTableColumn('# of Employers', 'companies.all.count'),
            AttributeTableColumn('Contact Name', 'contact.get_full_name'),
            AttributeTableColumn('Contact #', 'contact.phone'),
            AttributeTableColumn('Address', 'contact.get_full_address'),
            AttributeTableColumn('City', 'contact.city'),
            AttributeTableColumn('State', 'contact.state'),
            AttributeTableColumn('Zip', 'contact.zip'),
            ActionTableColumn(
                'Actions',
                actions=[ActionItem(
                    'Edit Payor/TPA',
                    GenesisTableLink(
                        edit_link,
                        url_args=url_args + [
                            GenesisTableLinkAttrArg('pk')
                        ]
                    )
                )]
            )
        ]

    def get_above_table_items(self):
        group = self.get_group()
        if group:
            if self.request.user.is_admin():
                import_link = 'accounts:manage-groups-payors-import'
                add_link = 'accounts:manage-groups-payors-create'
                del_link = 'accounts:manage-groups-payors-batch-delete'
                link_args = [group.id]
            else:
                import_link = 'accounts:manage-payors-import'
                add_link = 'accounts:manage-payors-create'
                del_link = 'accounts:manage-payors-batch-delete'
                link_args = []
            add_url = reverse(add_link, args=link_args)
            import_url = reverse(import_link, args=link_args)
            del_url = reverse(del_link, args=link_args)
            above_table_content_items = [
                GenesisAboveTableButton('Add Payor/TPA', add_url),
                GenesisAboveTableButton('Import Payors/TPA', import_url),
                GenesisAboveTableDropdown(
                    [GenesisDropdownOption('Delete', del_url)],
                    required_user_types=['admin']
                )
            ]
        else:
            above_table_content_items = []
        return above_table_content_items

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
        if group:
            page_title = 'Manage Payors/TPAs for {}'.format(group)
        else:
            page_title = 'Manage Payors/TPAs'
        return page_title

    def get_queryset(self):
        group = self.get_group()
        if group:
            return group.payors.all()
        assert self.request.user.is_admin()
        return Payor.objects.all()


tester = user_passes_test(
    lambda u: check_user_type(u, ['Admin', 'Professional'])
)
main = login_required(tester(PayorTableView.as_view()))


@user_passes_test(lambda u: check_user_type(u, ['Admin', 'Professional']))
def add(request, group_id=None):
    try:
        if group_id:
            assert request.user.is_admin()
            group = GenesisGroup.objects.get(pk=group_id)
            page_title = "Add Payor/TPA for %s" % group
        else:
            assert request.user.is_professional()
            group = request.user.professional_profile.parent_group
            page_title = "Add Payor/TPA"
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
                'Payors',
                reverse('accounts:manage-groups-payors',
                        args=[group.pk]))
        ]
    else:
        breadcrumbs = []

    return generic_form(
        request,
        form_class=PayorForm,
        page_title=page_title,
        system_message="The payor/TPA has been created.",
        breadcrumbs=breadcrumbs,
        form_kwargs={'initial_group': group})


@user_passes_test(lambda u: check_user_type(u, ['Admin', 'Professional']))
def import_csv(request, group_id=None):
    try:
        if group_id:
            assert request.user.is_admin()
            group = GenesisGroup.objects.get(id=group_id)
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
                'Payors',
                reverse('accounts:manage-groups-payors',
                        args=[group.pk]))
        ]
    else:
        breadcrumbs = []

    return generic_form(
        request,
        form_class=ImportPayorsForm,
        form_kwargs={'initial_group': group},
        page_title='Import Payors/TPA for %s' % group,
        breadcrumbs=breadcrumbs,
        system_message='The Payors/TPA have been imported')


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
        system_message='The selected payors have been deleted.',
        batch_queryset=group.payors.all(),
        batch=True,
    )


@login_required
@user_passes_test(lambda u: check_user_type(u, ['Admin', 'Professional']))
def edit(request, payor_id, group_id=None):
    try:
        if group_id:
            assert request.user.is_admin()
            group = GenesisGroup.objects.get(pk=group_id)
        else:
            if request.user.is_admin():
                group = None
            else:
                group = request.user.professional_profile.parent_group
        if group:
            payor = group.payors.get(pk=payor_id)
        else:
            payor = Payor.objects.get(pk=payor_id)
        if not group:
            group = payor.group
    except (GenesisGroup.DoesNotExist,
            Payor.DoesNotExist,
            AssertionError) as e:
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
                'Payors',
                reverse('accounts:manage-groups-payors',
                        args=[group.pk])),
            Breadcrumb(
                'Payor: {0}'.format(payor.name),
                ''
            )
        ]
    else:
        breadcrumbs = []

    return generic_form(
        request,
        form_class=PayorForm,
        page_title='Edit %s' % payor,
        system_message="The payor/TPA has been updated.",
        breadcrumbs=breadcrumbs,
        form_kwargs={'instance': payor, 'initial_group': group})
