from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse

from genesishealth.apps.alerts.forms import (
    PatientAlertForm, BatchEnableDisableForm)
from genesishealth.apps.alerts.models import PatientAlert
from genesishealth.apps.utils.class_views import (
    GenesisTableView, AttributeTableColumn, ActionTableColumn,
    ActionItem, GenesisTableLink, GenesisTableLinkAttrArg,
    GenesisDropdownOption, GenesisAboveTableButton,
    GenesisAboveTableDropdown)
from genesishealth.apps.utils.request import (
    check_user_type, debug_response)
from genesishealth.apps.utils.views import (generic_form, generic_delete_form)


class AlertTableView(GenesisTableView):
    def create_columns(self):
        return [
            AttributeTableColumn('Name', 'name'),
            AttributeTableColumn(
                'Phone Number', 'phone_number', sortable=False),
            AttributeTableColumn('Email', 'email'),
            AttributeTableColumn('Active', 'active'),
            ActionTableColumn(
                'Actions',
                actions=[
                    ActionItem(
                        'Edit Alert',
                        GenesisTableLink(
                            'alerts:alerts-edit',
                            url_args=[GenesisTableLinkAttrArg('pk')]
                        )
                    )
                ]
            )
        ]

    def get_above_table_items(self):
        return [
            GenesisAboveTableButton('Add Alert', reverse('alerts:alerts-new')),
            GenesisAboveTableDropdown(
                [GenesisDropdownOption(
                    'Enable', reverse('alerts:batch-enable')),
                 GenesisDropdownOption(
                    'Disable', reverse('alerts:batch-disable')),
                 GenesisDropdownOption(
                    'Delete', reverse('alerts:batch-delete'))]
            )
        ]

    def get_page_title(self):
        return 'Alerts'

    def get_queryset(self):
        return self.request.user.created_patientalerts.all()


test = user_passes_test(
    lambda u: check_user_type(u, ['Patient']))
main = test(AlertTableView.as_view())


@user_passes_test(lambda u: check_user_type(u, ['Patient']))
def new(request):
    kwargs = {
        'form_class': PatientAlertForm,
        'page_title': 'New Alert',
        'system_message': 'The alert has been created.',
        'form_kwargs': {'requester': request.user}}
    return generic_form(request, **kwargs)


@user_passes_test(lambda u: check_user_type(u, ['Patient']))
def edit(request, alert_id):
    try:
        alert = request.user.get_profile().get_alerts().get(pk=alert_id)
    except PatientAlert.DoesNotExist as e:
        return debug_response(e)

    return generic_form(
        request,
        form_class=PatientAlertForm,
        page_title='Edit Alert',
        system_message='The alert has been updated.',
        form_kwargs={'requester': request.user, 'instance': alert},
        extra_head_template='alerts/js/edit.html')


@user_passes_test(lambda u: check_user_type(u, ['Patient']))
def batch_change_status(request, enable):
    return generic_form(
        request,
        form_class=BatchEnableDisableForm,
        form_kwargs={'enable': enable},
        system_message='The selected alerts have been {}.'.format(
            'enabled' if enable else 'disabled'),
        go_back_until=['manage-alerts'],
        batch=True,
        only_batch_input=True,
        batch_queryset=request.user.get_profile().get_alerts()
    )


@user_passes_test(lambda u: check_user_type(u, ['Patient']))
def batch_delete(request):
    return generic_delete_form(
        request,
        system_message='The selected alerts have been deleted.',
        batch=True,
        batch_queryset=request.user.get_profile().get_alerts()
    )
