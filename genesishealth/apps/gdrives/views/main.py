from django import forms
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.urls import reverse

from genesishealth.apps.accounts.models import GenesisGroup, PatientProfile
from genesishealth.apps.gdrives.breadcrumbs import get_device_breadcrumbs
from genesishealth.apps.gdrives.forms import (
    AssignDeviceForm, GDriveForm, GDriveAssignForm,
    GDriveImportForm, GDriveInspectionForm, GDriveInspectionRecordForm,
    GDriveReworkRecordForm, ImportDevicesForm, RecoverReadingsForm)
from genesishealth.apps.gdrives.models import GDrive
from genesishealth.apps.gdrives.views.base import GetDeviceMixin
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.class_views import (
    AttributeTableColumn, GenesisTableView, GenesisFormView, GenesisFormMixin)
from genesishealth.apps.utils.class_views.csv_import import (
    CSVImportForm, CSVImportView)
from genesishealth.apps.utils.forms import GenesisForm
from genesishealth.apps.utils.request import (
    admin_user, check_user_type, debug_response, redirect_with_message)
from genesishealth.apps.utils.views import (
    generic_form, generic_delete_form)


test = user_passes_test(
    lambda u: check_user_type(u, ['Admin']))


@user_passes_test(admin_user)
def import_devices(request, group_id=None):
    group = None
    if group_id:
        try:
            group = GenesisGroup.objects.get(pk=group_id)
        except GenesisGroup.DoesNotExist as e:
            return debug_response(e)
        else:
            form_kwargs = {'group': group}
    else:
        form_kwargs = {}

    breadcrumbs = [
        Breadcrumb(
            'Business Partners',
            reverse('accounts:manage-groups')),
        Breadcrumb(
            'Business Partner: {0}'.format(group.name),
            reverse('accounts:manage-groups-detail',
                    args=[group.pk])),
        Breadcrumb(
            'Devices'.format(group.name),
            reverse('accounts:manage-groups-devices',
                    args=[group.pk])),
    ]

    return generic_form(
        request,
        page_title='Import Devices',
        form_class=ImportDevicesForm,
        form_kwargs=form_kwargs,
        breadcrumbs=breadcrumbs,
        system_message='The devices have been imported.')


class AssignByCSVView(GenesisFormView):
    form_class = GDriveAssignForm
    go_back_until = ['gdrives:available']
    success_message = "The devices have been assigned."
    page_title = "Assign Devices"

    def _get_breadcrumbs(self):
        return [
            Breadcrumb('Available Devices', reverse('gdrives:available'))
        ]
assign_by_csv = test(AssignByCSVView.as_view())


@user_passes_test(lambda u: check_user_type(u, ['Admin', 'Professional']))
def new(request, group_id=None):
    try:
        if group_id:
            assert request.user.is_admin()
            group = GenesisGroup.objects.get(pk=group_id)
        else:
            if request.user.is_professional():
                group = request.user.professional_profile.parent_group
            else:
                group = None
    except (GenesisGroup.DoesNotExist, AssertionError) as e:
        return debug_response(e)

    if request.user.is_admin():
        if group:
            breadcrumbs = [
                Breadcrumb(
                    'Business Partners',
                    reverse('accounts:manage-groups')),
                Breadcrumb(
                    'Business Partner: {0}'.format(group.name),
                    reverse('accounts:manage-groups-detail',
                            args=[group.pk])),
                Breadcrumb(
                    'Devices'.format(group.name),
                    reverse('accounts:manage-groups-devices',
                            args=[group.pk])),
            ]
        else:
            breadcrumbs = [
                Breadcrumb('New Devices', reverse('gdrives:new-devices'))
            ]
    else:
        breadcrumbs = []

    return generic_form(
        request,
        form_class=GDriveForm,
        form_kwargs={'initial_group': group},
        page_title='Add Device',
        breadcrumbs=breadcrumbs,
        system_message='The device has been created.')


@user_passes_test(lambda u: check_user_type(u, ['Admin', 'Professional']))
def edit(request, device_id):
    try:
        if request.user.is_professional():
            group = request.user.professional_profile.parent_group
            device = group.gdrives.get(pk=device_id)
        else:
            device = GDrive.objects.get(pk=device_id)
            group = device.group
    except GDrive.DoesNotExist as e:
        return debug_response(e)

    if request.user.is_admin():
        if group:
            breadcrumbs = [
                Breadcrumb(
                    'Business Partners',
                    reverse('accounts:manage-groups')),
                Breadcrumb(
                    'Business Partner: {0}'.format(group.name),
                    reverse('accounts:manage-groups-detail',
                            args=[group.pk])),
                Breadcrumb(
                    'Devices'.format(group.name),
                    reverse('accounts:manage-groups-devices',
                            args=[group.pk])),
            ]
        else:
            breadcrumbs = [
                Breadcrumb('Devices', reverse('gdrives:index'))
            ]
    else:
        breadcrumbs = []

    return generic_form(
        request,
        form_class=GDriveForm,
        page_title='Edit Device',
        system_message='The device has been updated.',
        form_kwargs={'instance': device, 'initial_group': group},
        breadcrumbs=breadcrumbs,
        delete_view_args=[device.id])


@user_passes_test(lambda u: check_user_type(u, ['Admin', 'Professional']))
def delete(request, device_id):
    try:
        if request.user.is_professional():
            group = request.user.professional_profile.parent_group
            device = group.gdrives.get(pk=device_id)
        else:
            device = GDrive.objects.get(pk=device_id)
            group = device.group
    except GDrive.DoesNotExist as e:
        return debug_response(e)

    if request.user.is_admin():
        if group:
            breadcrumbs = [
                Breadcrumb(
                    'Business Partners',
                    reverse('accounts:manage-groups')),
                Breadcrumb(
                    'Business Partner: {0}'.format(group.name),
                    reverse('accounts:manage-groups-detail',
                            args=[group.pk])),
                Breadcrumb(
                    'Devices'.format(group.name),
                    reverse('accounts:manage-groups-devices',
                            args=[group.pk])),
            ]
        else:
            breadcrumbs = [
                Breadcrumb('Devices', reverse('gdrives:index'))
            ]
    else:
        breadcrumbs = []

    if device.readings.count() > 0:
        extra_delete_warning = (
            'Note: This device has readings associated with it.  If you '
            'delete it, the readings will have no device associated '
            'with them.')
    else:
        extra_delete_warning = None

    return generic_delete_form(
        request, device,
        breadcrumbs=breadcrumbs,
        go_back_until=[
            'gdrives:index', 'accounts:manage-groups-devices',
            'gdrives:patient-details'],
        extra_delete_warning=extra_delete_warning
    )


@user_passes_test(lambda u: check_user_type(u, ['Admin', 'Professional']))
def assign(request, device_id):
    try:
        if request.user.is_professional():
            device = request.user.professional_profile.\
                parent_group.gdrives.get(pk=device_id)
        else:
            device = GDrive.objects.get(pk=device_id)
    except GDrive.DoesNotExist as e:
        return debug_response(e)

    return generic_form(
        request,
        form_class=AssignDeviceForm,
        form_kwargs={'instance': device},
        page_title="Assign Device %s to a Patient" % device.meid,
        system_message="The device has been assigned.")


@user_passes_test(lambda u: check_user_type(u, ['Admin', 'Professional']))
def assign_to_patient(request, device_id, patient_id):
    try:
        if request.user.is_professional():
            patient = request.user.professional_profile.\
                get_patients().get(pk=patient_id)
            device = request.user.professional_profile.\
                parent_group.get_available_devices(patient, True).get(
                    pk=device_id)
        else:
            device = GDrive.objects.get(pk=device_id)
            patient = PatientProfile.myghr_patients.get_users().get(
                pk=patient_id)
    except (GDrive.DoesNotExist, User.DoesNotExist) as e:
        return debug_response(e)

    patient.patient_profile.register_device(device)

    return redirect_with_message(
        request,
        reverse('gdrives:patient-details', args=[patient.pk]),
        'The device has been assigned.',
        ['gdrives:detail'])


@user_passes_test(lambda u: check_user_type(u, ['Admin', 'Professional']))
def unassign(request, device_id):
    try:
        if request.user.is_professional():
            device = request.user.professional_profile.\
                parent_group.get_devices(group_only=True).get(pk=device_id)
        else:
            device = GDrive.objects.get(pk=device_id)
        assert device.patient is not None
        patient = device.patient
    except (GDrive.DoesNotExist, AssertionError) as e:
        return debug_response(e)

    device.unregister()

    return redirect_with_message(
        request,
        reverse('gdrives:patient-details', args=[patient.pk]),
        'The device has been unassigned.',
        ['gdrives:detail'])


@user_passes_test(admin_user)
def recover_readings(request, device_id):
    device = GDrive.objects.get(pk=device_id)
    breadcrumbs = get_device_breadcrumbs(device, request.user)
    return generic_form(
        request,
        form_class=RecoverReadingsForm,
        form_kwargs={'device': device},
        page_title='Recover Readings for Device {0}'.format(device.meid),
        breadcrumbs=breadcrumbs,
        system_message="The readings have been recovered.")


class GDriveValidateFormView(GenesisFormView, GetDeviceMixin):
    form_class = GDriveInspectionRecordForm
    go_back_until = ['gdrives:index']
    success_message = 'The device has been validated and marked available.'

    def get_form_kwargs(self):
        kwargs = super(GDriveValidateFormView, self).get_form_kwargs()
        kwargs['requester'] = self.request.user
        kwargs['device'] = self.get_device()
        return kwargs
validate = user_passes_test(admin_user)(
    GDriveValidateFormView.as_view())


class GDriveImportFormView(GenesisFormView):
    form_class = GDriveImportForm
    success_message = 'The devices have been added.'
    page_title = 'Import Devices'

    def _get_breadcrumbs(self):
        return [
            Breadcrumb('Devices', reverse('gdrives:new-devices'))
        ]

    def get_success_url(self, form):
        return reverse('gdrives:new-devices')
import_csv = user_passes_test(admin_user)(
    GDriveImportFormView.as_view())


class GDriveReworkFormView(GenesisTableView, GenesisFormMixin, GetDeviceMixin):
    form_class = GDriveReworkRecordForm
    go_back_until = ['gdrives:detail']
    success_message = 'The device has been reworked.'
    template_name = 'gdrives/rework.html'

    def create_columns(self):
        return [
            AttributeTableColumn(
                'Non-Conformity',
                'get_problem_str',
                proxy_field='non_conformity_types.name'),
            AttributeTableColumn(
                'Description', 'description'),
            AttributeTableColumn(
                'Datetime Added',
                'datetime_added',
                default_sort=True,
                default_sort_direction='desc'),
            AttributeTableColumn(
                'Added By',
                'added_by.get_reversed_name',
                proxy_field='added_by.last_name'
            )
        ]

    def get_breadcrumbs(self):
        device = self.get_device()
        return get_device_breadcrumbs(device, self.request.user)

    def get_context_data(self, **kwargs):
        if 'form' not in kwargs:
            kwargs['form'] = self.get_form()
        if 'previous_notes' not in kwargs:
            kwargs['previous_notes'] = \
                self.get_device().rework_records.order_by('datetime_reworked')
        return super(GDriveReworkFormView, self).get_context_data(**kwargs)

    def get_form_kwargs(self):
        kwargs = super(GDriveReworkFormView, self).get_form_kwargs()
        kwargs['requester'] = self.request.user
        kwargs['device'] = self.get_device()
        return kwargs

    def get_page_title(self):
        return 'Rework Device {0}'.format(self.get_device().meid)

    def get_queryset(self):
        return self.get_device().non_conformities.all()

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
rework_device = user_passes_test(admin_user)(
    GDriveReworkFormView.as_view())


class GDriveInspectionView(GenesisFormView, GetDeviceMixin):
    form_class = GDriveInspectionForm
    template_name = 'gdrives/inspect_device.html'

    def get_form_kwargs(self):
        kwargs = super(GDriveInspectionView, self).get_form_kwargs()
        kwargs['device'] = self.get_device()
        kwargs['requester'] = self.request.user
        return kwargs

    def _get_page_title(self):
        return 'Inspect Device {0}'.format(self.get_device().meid)

    def get_success_message(self, form):
        if form.cleaned_data['disposition'] is None:
            return 'The device has been inspected and made available.'
        return 'The device has been marked as non-conforming.'

    def get_success_url(self, form):
        return reverse('gdrives:detail', args=[self.get_device().pk])
inspect_device = user_passes_test(admin_user)(
    GDriveInspectionView.as_view())


class VitalCareAssignDevicesLineForm(GenesisForm):
    patient = forms.ModelChoiceField(
        queryset=PatientProfile.objects.all(),
        to_field_name='insurance_identifier')
    device = forms.ModelChoiceField(
        queryset=GDrive.objects.filter(patient__isnull=True),
        to_field_name='meid')


class RocketHealthAssignDevicesLineForm(GenesisForm):
    patient = forms.ModelChoiceField(
        queryset=PatientProfile.objects.all(),
        to_field_name='insurance_identifier')
    device = forms.ModelChoiceField(
        queryset=GDrive.objects.filter(patient__isnull=True),
        to_field_name='meid')


class GenesisAssignDevicesLineForm(GenesisForm):
    patient = forms.ModelChoiceField(
        queryset=PatientProfile.objects.all(),
        to_field_name='user__id')
    device = forms.ModelChoiceField(
        queryset=GDrive.objects.filter(patient__isnull=True),
        to_field_name='meid')


class AssignDevicesImportForm(CSVImportForm):
    show_template_link = False

    def get_column_names(self):
        if not hasattr(self, '_columns'):
            self.get_line_form_class_and_columns()
        return self._columns

    def get_line_form_class(self):
        if not hasattr(self, '_form_class'):
            self.get_line_form_class_and_columns()
        return self._form_class

    def get_line_form_class_and_columns(self):
        header = self.get_header(self.cleaned_data['doc'])
        first_header_cell = header[0][0]
        self._columns = {
            'FIRSTNAME': (
                'first_name', 'initial', 'last_name', 'date_of_birth',
                'address1', 'address2', 'city', 'state', 'zipcode', 'patient',
                'action', 'device', 'date_in', 'date_out'),
            'insurance_id': ('patient', 'epc_member_identifier', 'device'),
            'MEID': ('device', 'patient')
        }[first_header_cell]
        self._form_class = {
            'FIRSTNAME': VitalCareAssignDevicesLineForm,
            'insurance_id': RocketHealthAssignDevicesLineForm,
            'MEID': GenesisAssignDevicesLineForm
        }[first_header_cell]


class AssignDevicesImportView(CSVImportView):
    form_class = AssignDevicesImportForm
    success_message = "The devices have been assigned."
    go_back_until = ["gdrives:index"]
    page_title = "Assign Devices"

    def process_line(self, form, line):
        device = line['device']
        profile = line['patient']
        if device.is_available_to_patient(profile.user):
            device.register(profile.user)
assign_devices_import = user_passes_test(admin_user)(
    AssignDevicesImportView.as_view())
