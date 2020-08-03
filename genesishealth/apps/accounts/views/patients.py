import os

from datetime import timedelta
from json import dumps

from dateutil.parser import parse

from django import forms
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.urls import reverse
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils.timezone import now
from django.views.decorators.http import require_POST

from genesishealth.apps.accounts.breadcrumbs.patients import (
    get_patient_breadcrumbs, get_communication_breadcrumbs)
from genesishealth.apps.accounts.breadcrumbs.groups import (
    get_group_breadcrumbs)
from genesishealth.apps.accounts.forms.patients import (
    ActivateForm, BatchActivateForm, BatchAddToWatchListForm,
    BatchAssignPatientForm, BatchAssignToAPIPartnerForm, BatchDeactivateForm,
    BatchMigrateForm, BatchRecoverReadingsForm, BatchRemoveFromWatchListForm,
    BatchUnassignFromAPIPartnerForm, BatchUnassignPatientForm,
    DeactivateForm, ImportPatientForm, PatientForm, PatientWizardForm,
    UpdateNotesForm, PatientCommunicationForm, PatientCommunicationNoteForm,
    CallLogReportForm
)
from genesishealth.apps.accounts.models import (
    GenesisGroup, Note, PatientProfile)
from genesishealth.apps.accounts.views.base import GroupTableView
from genesishealth.apps.dropdowns.models import (
    CommunicationCategory, CommunicationSubcategory)
from genesishealth.apps.reports.views.main import (
    ReportView, PDFPrintURLResponse)
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.class_views import (
    ActionItem, ActionTableColumn, AttributeTableColumn,
    GenesisAboveTableButton, GenesisAboveTableDropdown, GenesisBaseDetailPane,
    GenesisDetailView, GenesisDropdownOption,
    GenesisTableLink, GenesisTableLinkAttrArg, GenesisTableView,
    GenesisFormView
)
from genesishealth.apps.utils.class_views.csv_import import (
    CSVImportForm, CSVImportView)
from genesishealth.apps.utils.forms import (
    GenesisForm, ZipField)
from genesishealth.apps.utils.request import (
    admin_user, check_user_type, debug_response, professional_user,
    redirect_with_message)
from genesishealth.apps.utils.us_states import US_STATES
from genesishealth.apps.utils.views import (
    generic_delete_form, generic_form)


class GetPatientMixin(object):
    def get_patient(self):
        if not hasattr(self, '_patient'):
            self._patient = User.objects.filter(
                patient_profile__isnull=False).get(
                pk=self.kwargs['patient_id'])
        return self._patient


class CaregiverTableView(GenesisTableView):
    def create_columns(self):
        return [
            AttributeTableColumn('Last Name', 'last_name'),
            AttributeTableColumn('First Name', 'first_name'),
            AttributeTableColumn(
                'Group/Employer', 'patient_profile.company.name'),
            AttributeTableColumn('Payor/TPA', 'patient_profile.company.payor'),
            AttributeTableColumn(
                'Contact #', 'patient_profile.contact.phone',
                sortable=False),
            ActionTableColumn(
                'Notes',
                actions=[
                    ActionItem(
                        'View Notes',
                        GenesisTableLink(
                            'accounts:manage-patients-notes',
                            url_args=[GenesisTableLinkAttrArg('pk')]
                        )
                    )
                ]
            ),
            ActionTableColumn(
                'Reports',
                actions=[
                    ActionItem(
                        'View Reports',
                        GenesisTableLink(
                            'reports:patient-index',
                            url_args=[GenesisTableLinkAttrArg('pk')]
                        )
                    ),
                    ActionItem(
                        'Edit Targets',
                        GenesisTableLink(
                            'health_information:edit-health-targets',
                            url_args=[GenesisTableLinkAttrArg('pk')]
                        )
                    )
                ]
            ),

        ]

    def get_above_table_items(self):
        return [
            GenesisAboveTableDropdown([
                GenesisDropdownOption(
                    'Add to Watch List',
                    reverse('accounts:batch-add-to-watch-list')),
                GenesisDropdownOption(
                    'Remove from Watch List',
                    reverse('accounts:batch-remove-from-watch-list')),
            ])
        ]

    def get_page_title(self):
        return 'My Patients'

    def get_queryset(self):
        return self.request.user.professional_profile.get_patients()


class PatientTableView(GroupTableView):
    extra_search_fields = [
        'patient_profile__insurance_identifier',
        'patient_profile__epc_member_identifier',
        'gdrives__meid',
        'id']

    def create_columns(self):
        group = self.get_group()
        if group is not None and group.is_no_pii:
            columns = [
                AttributeTableColumn(
                    'MEID',
                    'patient_profile.get_device.meid',
                    proxy_field='gdrives.meid',
                    cell_class='main'),
                AttributeTableColumn(
                    'Serial',
                    'patient_profile.get_device.device_id',
                    proxy_field='gdrives.device_id',),
                AttributeTableColumn(
                    'Patient', 'patient_profile.epc_member_identifier'),
                AttributeTableColumn(
                    'Patient Status',
                    'patient_profile.get_account_status_display',
                    searchable=False,
                    sortable=False),
                AttributeTableColumn(
                    'Last Reading',
                    'patient_profile.get_last_reading_date',
                    searchable=False,
                    sortable=False),
                AttributeTableColumn(
                    'Device Status',
                    'patient_profile.get_device.get_status_display',
                    searchable=False,
                    sortable=False)
            ]
        else:
            columns = [
                AttributeTableColumn(
                    'Last Name', 'last_name', cell_class='main'),
                AttributeTableColumn('First Name', 'first_name'),
                AttributeTableColumn('Payor/TPA',
                                     'patient_profile.company.payor.name'),
                AttributeTableColumn('Group/Employer',
                                     'patient_profile.company.name'),
                AttributeTableColumn(
                    'API Partner', 'patient_profile.get_partner_string'),
                AttributeTableColumn(
                    'Caregiver',
                    'patient_profile.get_caregiver.user.get_reversed_name'),
                AttributeTableColumn(
                    'Phone Number', 'patient_profile.contact.phone',
                    sortable=False)
            ]
            if self.request.user.is_admin():
                columns.append(
                    AttributeTableColumn(
                        'Last Reading Date',
                        'patient_profile.get_last_reading_display',
                        searchable=False
                    )
                )
        actions = [
            ActionTableColumn(
                'View',
                actions=[
                    ActionItem(
                        'Detail',
                        GenesisTableLink(
                            'accounts:manage-patients-detail',
                            url_args=[GenesisTableLinkAttrArg('pk')]
                        )
                    )
                ]
            )
        ]
        return columns + actions

    def get_above_table_items(self):
        options = [
            GenesisDropdownOption(
                'Assign to API Partner',
                reverse(
                    'accounts:manage-patients-batch-assign-api-partner')
            ),
            GenesisDropdownOption(
                'Unassign from API Partner',
                reverse(
                    'accounts:manage-patients-batch-unassign-api-partner')
            ),
            GenesisDropdownOption(
                'Migrate Readings',
                reverse(
                    'accounts:manage-patients-migrate-patient-readings')
            ),
            GenesisDropdownOption(
                'Recover Past Readings',
                reverse('accounts:manage-patients-recover-readings')
            ),
            GenesisDropdownOption(
                'Export to CSV',
                reverse('accounts:batch-csv-export'),
                direct_link=True
            ),
            GenesisDropdownOption(
                'Activate Patients',
                reverse('accounts:batch-activate-patients')
            ),
            GenesisDropdownOption(
                'Deactivate Patients',
                reverse('accounts:batch-deactivate-patients')
            )
        ]
        atc = []
        group = self.get_group()
        if group:
            add_link = reverse(
                'accounts:manage-groups-patients-create', args=[group.id])
            import_link = reverse(
                'accounts:manage-groups-patients-import', args=[group.id])
            atc.extend([
                GenesisAboveTableButton('Add Patient', add_link),
                GenesisAboveTableButton('Import Patients', import_link),
            ])
            if self.should_show_assigned():
                option_label = 'Unassign Patient'
                button_label = 'Show Unassigned'
                option_link = reverse(
                    'accounts:manage-groups-patients-batch-unassign',
                    args=[group.id])
                button_link = reverse(
                    'accounts:manage-groups-patients',
                    args=[group.id])
            else:
                option_label = 'Assign Patient'
                button_label = 'Show Assigned'
                option_link = reverse(
                    'accounts:manage-groups-patients-batch-assign',
                    args=[group.id])
                button_link = reverse(
                    'accounts:manage-groups-patients-assigned',
                    args=[group.id])
            options.append(
                GenesisDropdownOption(
                    option_label, option_link, no_redirect=True)
            )
            atc.append(
                GenesisAboveTableButton(button_label, button_link)
            )
        atc.append(GenesisAboveTableDropdown(options))
        return atc

    def get_breadcrumbs(self):
        group = self.get_group()
        if group:
            return get_group_breadcrumbs(group, self.request.user)
        return [
            Breadcrumb('Users', reverse('accounts:manage-users'))
        ]

    def get_page_title(self):
        group = self.get_group()
        if self.should_show_assigned():
            base = 'Manage Assigned Patients'
        else:
            base = 'Manage Unassigned Patients'
        if group:
            return '{} for {}'.format(base, group)
        return base

    def get_prefetch_fields(self):
        return (
            'patient_profile',
            'patient_profile__contact',
            'patient_profile__company',
            'patient_profile__company__contact',
            'patient_profile__company__payor',
            'patient_profile__company__payor__contact'
        )

    def get_queryset(self):
        queryset = PatientProfile.myghr_patients.get_users()
        group = self.get_group()
        if group:
            queryset = queryset.filter(patient_profile__group=group)
        if self.should_show_assigned():
            queryset = queryset.filter(
                patient_profile__professionals__isnull=False).distinct()
        else:
            queryset = queryset.filter(
                patient_profile__professionals__isnull=True).distinct()
        return queryset

    def should_show_assigned(self):
        return self.kwargs.get('show_assigned', False)


@user_passes_test(lambda u: check_user_type(u, ['Admin', 'Professional']))
def main(request, *args, **kwargs):
    if request.user.is_professional():
        return CaregiverTableView.as_view()(request, *args, **kwargs)
    if request.user.is_admin():
        return PatientTableView.as_view()(request, *args, **kwargs)


@user_passes_test(lambda u: check_user_type(u, ['Admin']))
def add(request, group_id=None):
    if request.user.is_admin():
        if group_id is None:
            raise Http404
        group = GenesisGroup.objects.get(pk=group_id)
        breadcrumbs = get_group_breadcrumbs(group, request.user)
        breadcrumbs.append(
            Breadcrumb(
                'Patients'.format(group.name),
                reverse('accounts:manage-groups-patients',
                        args=[group.pk]))
        )
    else:
        if group_id is not None:
            raise Http404
        group = request.user.professional_profile.parent_group
        breadcrumbs = [
            Breadcrumb(
                'Patients'.format(group.name),
                reverse('accounts:manage-patients'))
        ]
    company_data = {}
    for company in group.companies.all():
        company_data[company.id] = {
            'bin': company.bin_id,
            'pcn': company.pcn_id
        }
    return generic_form(
        request,
        form_class=PatientWizardForm,
        form_kwargs={'initial_group': group},
        extra_form_context={'company_json': dumps(company_data)},
        form_template='accounts/add_patient.html',
        page_title='Add Patient to {}'.format(group),
        system_message="The patient has been created.",
        breadcrumbs=breadcrumbs)


class PatientImportLineForm(GenesisForm):
    first_name = forms.CharField()
    initial = forms.CharField(required=False)
    last_name = forms.CharField()
    gender = forms.CharField()
    date_of_birth = forms.CharField(required=False)
    email = forms.EmailField(required=False)
    address1 = forms.CharField()
    address2 = forms.CharField(required=False)
    city = forms.CharField()
    state = forms.ChoiceField(choices=US_STATES, required=False)
    zip = ZipField()
    phone = forms.CharField(required=False, label="Primary phone")
    insurance_identifier = forms.CharField()
    insurance_suffix = forms.CharField(required=False)
    action = forms.CharField(required=False)
    epc_member_identifier = forms.CharField(required=False)
    existing_profile = forms.ModelChoiceField(
        queryset=PatientProfile.objects.all(),
        to_field_name='api_username',
        required=False)

    def clean_date_of_birth(self):
        dob = self.cleaned_data['date_of_birth']
        if dob:
            try:
                return parse(dob).date()
            except ValueError:
                raise forms.ValidationError(
                    "Invalid birthdate: {0}".format(dob))


class PatientImportForm(CSVImportForm):
    line_form_class = PatientImportLineForm
    columns = (
        'first_name', 'initial', 'last_name', 'gender', 'date_of_birth',
        'email', 'address1', 'address2', 'city', 'state', 'zip', 'phone',
        'insurance_identifier', 'insurance_suffix', 'action',
        'epc_member_identifier', 'existing_profile')

    company = forms.ModelChoiceField(
        queryset=None, required=False)

    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop('group')
        super(PatientImportForm, self).__init__(*args, **kwargs)
        self.fields['company'].queryset = self.group.companies.all()


class PatientImportView(CSVImportView):
    form_class = PatientImportForm
    success_message = "The patients have been imported."
    go_back_until = ["accounts:manage-groups-patients"]

    def get_form_kwargs(self):
        kwargs = super(PatientImportView, self).get_form_kwargs()
        kwargs['group'] = self.get_group()
        return kwargs

    def get_group(self):
        if not hasattr(self, '_group'):
            self._group = GenesisGroup.objects.get(
                pk=self.kwargs['group_id'])
        return self._group

    def _get_page_title(self):
        return "Import Patients for {0}".format(self.get_group())

    def process_line(self, form, line):
        print(line)
        clean_line = line.copy()
        del clean_line['existing_profile']
        del clean_line['action']
        del clean_line['insurance_suffix']
        clean_line['group'] = self.get_group()
        if form.cleaned_data['company']:
            company = form.cleaned_data['company']
            clean_line['company'] = company
            if company.default_pharmacy:
                clean_line['rx_partner'] = company.default_pharmacy
        if line['existing_profile']:
            profile = line['existing_profile']
            profile.update(save=True, **clean_line)
            user = profile.user
        else:
            user = PatientProfile.myghr_patients.create_user(
                **clean_line)
        user.patient_profile.set_phone_number(line['phone'])
        return user


import_csv = user_passes_test(
    lambda u: check_user_type(u, ['Admin', 'Professional']))(
    PatientImportView.as_view())


@user_passes_test(lambda u: check_user_type(u, ['Admin', 'Professional']))
def import_csv_old(request, group_id=None):
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
        breadcrumbs = get_group_breadcrumbs(group, request.user)
        breadcrumbs.append(
            Breadcrumb(
                'Patients'.format(group.name),
                reverse('accounts:manage-groups-patients',
                        args=[group.pk]))
        )
    else:
        breadcrumbs = [
            Breadcrumb(
                'Patients'.format(group.name),
                reverse('accounts:manage-patients'))
        ]

    view_kwargs = {
        "form_class": ImportPatientForm,
        "form_kwargs": {'initial_group': group, 'user': request.user},
        "page_title": "Import Patients",
        "system_message": "The patients have been imported.",
        "go_back_until": ['accounts:manage-groups-patients'],
        "breadcrumbs": breadcrumbs
    }
    if request.user.is_admin():
        view_kwargs['send_download_url'] = True
    return generic_form(request, **view_kwargs)


@user_passes_test(lambda u: check_user_type(u, ['Admin', 'Professional']))
def edit(request, patient_id, group_id=None):
    try:
        if group_id:
            assert request.user.is_admin()
            group = GenesisGroup.objects.get(pk=group_id)
            patient = group.get_patients().get(pk=patient_id)
        else:
            if request.user.is_professional():
                group = request.user.professional_profile.parent_group
                patient = request.user.professional_profile.get_patients(
                    ['edit-patient-profile']).get(pk=patient_id)
            else:
                patient = PatientProfile.myghr_patients.get_users().get(
                    pk=patient_id)
                group = patient.patient_profile.get_group()
    except (GenesisGroup.DoesNotExist, User.DoesNotExist, AssertionError) as e:
        return debug_response(e)

    breadcrumbs = get_patient_breadcrumbs(patient, request.user)

    return generic_form(
        request,
        form_class=PatientForm,
        page_title='Edit Patient {}'.format(patient.get_reversed_name()),
        system_message="The patient has been updated.",
        form_kwargs={'initial_group': group, 'instance': patient},
        breadcrumbs=breadcrumbs)


@user_passes_test(professional_user)
def notes(request, patient_id):
    form_kwargs = {'requester': request.user}
    try:
        form_kwargs['patient'] = patient = \
            request.user.professional_profile.get_patients().get(pk=patient_id)
    except User.DoesNotExist as e:
        return debug_response(e)

    c = {
        'patient': patient,
        'form': UpdateNotesForm(**form_kwargs),
        'notes': patient.notes_about.order_by('-date_created')
    }

    return render(request, 'accounts/manage/notes.html', c)


@user_passes_test(professional_user)
def update_note(request, patient_id, note_id=None):
    form_kwargs = {'requester': request.user}
    try:
        form_kwargs['patient'] = \
            request.user.professional_profile.get_patients().get(pk=patient_id)
        if note_id:
            form_kwargs['instance'] = note = Note.objects.get(pk=note_id)
            assert note.author == request.user
    except (User.DoesNotExist, AssertionError, Note.DoesNotExist) as e:
        return debug_response(e)

    return generic_form(
        request,
        form_class=UpdateNotesForm,
        form_kwargs=form_kwargs,
        system_message="Your note has been added.",
        go_back_until=['accounts:manage-patients-notes']
    )


@user_passes_test(professional_user)
def records(request, patient_id):
    try:
        patient = request.user.professional_profile.get_patients().get(
            pk=patient_id)
    except User.DoesNotExist as e:
        return debug_response(e)

    c = {'patient': patient}

    return render(request, 'accounts/manage/records.html', c)


class ActivatePatientView(GenesisFormView, GetPatientMixin):
    def get_form_class(self):
        return ActivateForm if self.is_activating() else DeactivateForm

    def get_form_kwargs(self):
        kwargs = super(ActivatePatientView, self).get_form_kwargs()
        kwargs['patient'] = self.get_patient()
        kwargs['requester'] = self.request.user
        return kwargs

    def _get_page_title(self):
        if self.is_activating():
            verb = "Activate"
        else:
            verb = "Deactivate"
        return "{0} {1}".format(verb, self.get_patient().get_reversed_name())

    def get_success_message(self, form):
        verb = "deactivated" if self.is_activating() else "activated"
        return "The patient has been {0}.".format(verb)

    def is_activating(self):
        return (self.get_patient().patient_profile.account_status !=
                PatientProfile.ACCOUNT_STATUS_ACTIVE)


activate_patient = user_passes_test(admin_user)(ActivatePatientView.as_view())


@user_passes_test(lambda u: check_user_type(u, ['Admin', 'Professional']))
def batch_assign(request, group_id=None):
    try:
        if group_id:
            assert request.user.is_admin()
            group = GenesisGroup.objects.get(pk=group_id)
        else:
            assert request.user.is_professional()
            group = request.user.professional_profile.parent_group
    except (GenesisGroup.DoesNotExist, AssertionError) as e:
        return debug_response(e)

    if request.user.is_admin():
        batch_queryset = group.get_patients()
    else:
        batch_queryset = request.user.professional_profile.get_patients()

    return generic_form(
        request,
        form_class=BatchAssignPatientForm,
        page_title='Assign Patients',
        system_message="The patients have been assigned.",
        form_kwargs={'professionals': group.get_professionals()},
        batch=True,
        batch_queryset=batch_queryset
    )


@user_passes_test(admin_user)
def batch_assign_to_partner(request):
    return generic_form(
        request,
        form_class=BatchAssignToAPIPartnerForm,
        page_title='Assign Patients to API Partner',
        system_message="The patients have been assigned.",
        batch=True,
        batch_queryset=PatientProfile.objects.get_users()
    )


@user_passes_test(admin_user)
def batch_unassign_from_partner(request):
    return generic_form(
        request,
        form_class=BatchUnassignFromAPIPartnerForm,
        page_title='Unassign Patients from API Partner',
        system_message="The patients have been unassigned.",
        batch=True,
        batch_queryset=PatientProfile.objects.get_users()
    )


@user_passes_test(admin_user)
def batch_migrate_to_api_partner(request):
    return generic_form(
        request,
        form_class=BatchMigrateForm,
        page_title='Migrate Readings to API Partner',
        system_message="The patients have been migrated.",
        batch=True,
        go_back_until=[
            'accounts:manage-patients', 'accounts:manage-groups-patients'],
        only_batch_input=True,
        batch_queryset=PatientProfile.objects.get_users()
    )


@user_passes_test(lambda u: check_user_type(u, ['Admin', 'Professional']))
def batch_unassign(request, group_id=None):
    try:
        if group_id:
            assert request.user.is_admin()
            group = GenesisGroup.objects.get(pk=group_id)
        else:
            assert request.user.is_professional()
            group = request.user.professional_profile.parent_group
    except (GenesisGroup.DoesNotExist, AssertionError) as e:
        return debug_response(e)

    if request.user.is_admin():
        batch_queryset = group.get_patients()
    else:
        batch_queryset = request.user.professional_profile.get_patients()

    return generic_form(
        request,
        form_class=BatchUnassignPatientForm,
        page_title='Assign Patients',
        system_message="The patients have been unassigned.",
        batch=True,
        go_back_until=[
            'accounts:manage-patients', 'accounts:manage-groups-patients'],
        only_batch_input=True,
        batch_queryset=batch_queryset
    )


@user_passes_test(admin_user)
def batch_activate_patient(request):
    return generic_form(
        request,
        form_class=BatchActivateForm,
        page_title='Activate Patients',
        system_message="The patients have been activated.",
        batch=True,
        form_kwargs={'requester': request.user},
        go_back_until=[
            'accounts:manage-patients-detail',
            'accounts:manage-groups-patients'],
        batch_queryset=PatientProfile.objects.get_users()
    )


@user_passes_test(admin_user)
def batch_deactivate_patient(request):
    return generic_form(
        request,
        form_class=BatchDeactivateForm,
        page_title='Deactivate Patients',
        system_message="The patients have been deactivated.",
        batch=True,
        form_kwargs={'requester': request.user},
        go_back_until=[
            'accounts:manage-patients', 'accounts:manage-groups-patients'],
        batch_queryset=PatientProfile.objects.get_users()
    )


class WatchListTableView(GenesisTableView):
    additional_js_templates = ['accounts/watchlist_js.html']

    def create_columns(self):
        return [
            AttributeTableColumn(
                'Patient Name', 'get_reversed_name', cell_class='main'),
            AttributeTableColumn('Group/Employer', 'patient_profile.company'),
            AttributeTableColumn('Payor/TPA', 'patient_profile.company.payor'),
            AttributeTableColumn('Contact #', 'patient_profile.contact.phone',
                                 sortable=False),
            ActionTableColumn(
                'Notes',
                actions=[
                    ActionItem(
                        'View Notes',
                        GenesisTableLink(
                            'accounts:manage-patients-notes',
                            url_args=[GenesisTableLinkAttrArg('pk')])
                    )
                ]
            ),
            ActionTableColumn(
                'Reports',
                actions=[
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
        return [
            GenesisAboveTableDropdown([
                GenesisDropdownOption(
                    'Remove from Watch List',
                    reverse('accounts:batch-remove-from-watch-list')
                )
            ])
        ]

    def get_page_title(self):
        return 'My Watch List'

    def get_queryset(self):
        prof = self.request.user.professional_profile
        return User.objects.filter(patient_profile__in=prof.watch_list.all())


prof_test = user_passes_test(professional_user)

watch_list = prof_test(WatchListTableView.as_view())


@user_passes_test(professional_user)
def batch_add_to_watch_list(request):
    return generic_form(
        request,
        form_class=BatchAddToWatchListForm,
        form_kwargs={'requester': request.user},
        system_message='The patients have been added to your watch list.',
        go_back_until=['accounts:manage-patients'],
        batch=True,
        only_batch_input=True,
        batch_queryset=request.user.professional_profile.get_patients())


@user_passes_test(professional_user)
def batch_remove_from_watch_list(request):
    return generic_form(
        request,
        form_class=BatchRemoveFromWatchListForm,
        form_kwargs={'requester': request.user},
        system_message='The patients have been removed to your watch list.',
        go_back_until=['accounts:manage-patients'],
        batch=True,
        only_batch_input=True,
        batch_queryset=request.user.professional_profile.get_patients())


@user_passes_test(lambda u: check_user_type(u, ['Admin', 'Professional']))
def batch_delete(request):
    if request.user.is_admin:
        batch_queryset = PatientProfile.myghr_patients.get_users().filter(
            patient_profile__isnull=False)
    else:
        batch_queryset = request.user.professional_profile.get_patients()
    return generic_delete_form(
        request,
        system_message='The selected patients have been deleted.',
        page_title='Delete patients',
        batch=True,
        batch_queryset=batch_queryset)


@user_passes_test(lambda u: check_user_type(u, ['Admin']))
def batch_recover_readings(request):
    return generic_form(
        request,
        form_class=BatchRecoverReadingsForm,
        page_title='Recover Readings',
        system_message=(
            "Readings for the selected patients have been recovered."),
        batch=True,
        batch_queryset=PatientProfile.objects.get_users()
    )


@require_POST
@user_passes_test(admin_user)
def batch_csv_export(request):
    # Create CSV
    batch_ids = request.POST.get('batch_ids').split(',')
    patients = User.objects.filter(pk__in=batch_ids)
    PatientProfile.generate_csv('/tmp/genesiscsv', patients)
    # get content
    with open('/tmp/genesiscsv') as f:
        content = f.read()
    # delete CSV
    os.remove('/tmp/genesiscsv')
    # render response
    response = HttpResponse(content, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="export.csv"'
    return response


class PatientInformationPane(GenesisBaseDetailPane):
    template_name = 'accounts/patients/detail_panes/information.html'
    pane_title = "Information"


class PatientShippingPane(GenesisBaseDetailPane):
    template_name = 'accounts/patients/detail_panes/shipping.html'
    pane_title = "Account Snapshot"


class PatientLoginPane(GenesisBaseDetailPane):
    template_name = 'accounts/patients/detail_panes/login_activity.html'
    pane_title = "People Snapshot"


class PatientGlucoseStatisticPane(GenesisBaseDetailPane):
    template_name = 'accounts/patients/detail_panes/reading_history.html'
    pane_title = "Glucose Statistics"


class PatientDetailView(GenesisDetailView):
    pane_classes = (
        PatientInformationPane, PatientShippingPane, PatientLoginPane,
        PatientGlucoseStatisticPane)

    def __init__(self, *args, **kwargs):
        self._patient = None
        super(PatientDetailView, self).__init__(*args, **kwargs)

    def get_breadcrumbs(self):
        patient = self.get_patient()
        return get_patient_breadcrumbs(
            patient, self.request.user, include_detail=False)

    def get_buttons(self):
        patient = self.get_patient()
        if (patient.patient_profile.account_status ==
                PatientProfile.ACCOUNT_STATUS_ACTIVE):
            activate_text = 'Deactivate'
        else:
            activate_text = 'Activate'
        return [
            GenesisAboveTableButton(
                'Password',
                reverse('accounts:manage-login', args=[patient.pk])),
            GenesisAboveTableButton(
                'Account',
                reverse('accounts:manage-patients-edit', args=[patient.pk])),
            GenesisAboveTableButton(
                activate_text,
                reverse('accounts:manage-patients-activate', args=[patient.pk])
            ),
            GenesisAboveTableButton(
                'Reports',
                reverse('reports:patient-index', args=[patient.pk])
            ),
            GenesisAboveTableButton(
                'Devices',
                reverse('gdrives:patient-details', args=[patient.pk])),
            GenesisAboveTableButton(
                'Communications',
                reverse('accounts:patient-communications', args=[patient.pk])),
            GenesisAboveTableButton(
                'EPC Orders',
                reverse('epc:patient-orders', args=[patient.pk])),
            GenesisAboveTableButton(
                'Orders',
                reverse('accounts:patient-orders', args=[patient.pk]))

        ]

    def get_page_title(self):
        return 'Manage Patient {0}'.format(
            self.get_patient().get_reversed_name())

    def get_patient(self):
        if self._patient is None:
            self._patient = User.objects.filter(
                patient_profile__isnull=False).get(
                pk=self.kwargs['patient_id'])
        return self._patient

    def get_pane_context(self):
        patient = self.get_patient()
        cutoff = now() - timedelta(days=180)
        last_180 = patient.glucose_readings.filter(
            reading_datetime_utc__gt=cutoff).count()
        return {
            'patient': patient,
            'last_login': patient.patient_profile.get_last_login(),
            'logins_last_six_months': patient.login_records.filter(
                datetime__gt=now() - timedelta(days=182)).count(),
            'recent_readings': patient.glucose_readings.order_by(
                '-reading_datetime_utc')[:4],
            'readings_last_180': last_180
        }


test = user_passes_test(admin_user)
detail = test(PatientDetailView.as_view())


class PatientCommunicationsTableView(GenesisTableView, GetPatientMixin):
    def create_columns(self):
        patient = self.get_patient()
        return [
            AttributeTableColumn(
                'Datetime Added',
                'datetime_added',
                default_sort_direction='desc',
                default_sort=True),
            AttributeTableColumn(
                'Added By',
                'added_by.get_reversed_name',
                proxy_field='added_by.last_name'),
            AttributeTableColumn('Subject', 'subject'),
            AttributeTableColumn('Last Updated', 'datetime_updated'),
            AttributeTableColumn(
                'Last Updated By',
                'last_updated_by.get_reversed_name',
                proxy_field='last_updated_by.last_name'),
            AttributeTableColumn('Status', 'status.name'),
            ActionTableColumn(
                'View',
                actions=[
                    ActionItem(
                        'View',
                        GenesisTableLink(
                            'accounts:edit-communication',
                            url_args=[patient.pk,
                                      GenesisTableLinkAttrArg('pk')])
                    ),
                    ActionItem(
                        'Report',
                        GenesisTableLink(
                            'accounts:communication-report-pdf',
                            url_args=[patient.pk,
                                      GenesisTableLinkAttrArg('pk')],
                            prefix='')
                    )
                ]
            )
        ]

    def get_above_table_items(self):
        patient = self.get_patient()
        above_table = [
            GenesisAboveTableButton(
                'Add Communication',
                reverse('accounts:new-communication',
                        args=[patient.pk])),
        ]
        return above_table

    def get_breadcrumbs(self):
        return get_patient_breadcrumbs(self.get_patient(), self.request.user)

    def get_page_title(self):
        return 'Communications for {0}'.format(
            self.get_patient().get_reversed_name())

    def get_queryset(self):
        return self.get_patient().communications.all()


communications = test(PatientCommunicationsTableView.as_view())


class NewPatientCommunicationFormView(GenesisFormView, GetPatientMixin):
    form_class = PatientCommunicationForm
    template_name = 'accounts/patients/patient_communication.html'
    prefix = 'communication'

    def form_invalid(self, form, note_form):
        return self.render_to_response(
            self.get_context_data(form=form, note_form=note_form))

    def form_valid(self, form, note_form):
        communication = form.save()
        note_form.save(communication)
        return redirect_with_message(
            self.request,
            self.get_success_url(form, note_form),
            'The communication has been added.',
            go_back_until=['accounts:patient-communications',
                           'accounts:communications'])

    def _get_breadcrumbs(self):
        patient = self.get_patient()
        requester = self.request.user
        breadcrumbs = get_patient_breadcrumbs(patient, requester)
        breadcrumbs.append(
            Breadcrumb('Communications',
                       reverse('accounts:patient-communications',
                               args=[patient.pk]))
        )
        return breadcrumbs

    def get_context_data(self, **kwargs):
        context = super(NewPatientCommunicationFormView, self)\
            .get_context_data(**kwargs)
        if 'note_form' not in context:
            context['note_form'] = self.get_note_form()
        context['subcategories'] = CommunicationSubcategory.objects.all()
        context['serialized_cat_data'] = dumps({
            category.id: [subcategory.id for
                          subcategory in category.subcategories.all()]
            for category in CommunicationCategory.objects.filter(
                is_active=True)
        })
        return context

    def get_form_kwargs(self):
        kwargs = super(NewPatientCommunicationFormView, self).get_form_kwargs()
        kwargs['requester'] = self.request.user
        kwargs['patient'] = self.get_patient()
        return kwargs

    def get_note_form(self):
        return PatientCommunicationNoteForm(
            **self.get_note_form_kwargs())

    def get_note_form_kwargs(self):
        kwargs = {
            'prefix': 'note',
            'requester': self.request.user,
        }
        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES
            })
        return kwargs

    def _get_page_title(self):
        return 'New Communication for {0}'.format(
            self.get_patient().get_reversed_name())

    def get_success_url(self, form, note_form):
        should_show_complaint = bool(filter(
            lambda x: x.is_device,
            note_form.cleaned_data['replacements']
        ))
        if should_show_complaint:
            patient = self.get_patient()
            device = patient.patient_profile.get_device()
            if device:
                complaints = device.complaints.order_by('-datetime_added')
                if complaints.count() > 0:
                    return reverse(
                        'gdrives:edit-complaint',
                        args=[device.pk, complaints[0].pk]
                    )
                return reverse('gdrives:new-complaint', args=[device.pk])

    def post(self, request, *args, **kwargs):
        communication_form = self.get_form()
        note_form = self.get_note_form()
        if communication_form.is_valid() and note_form.is_valid():
            return self.form_valid(communication_form, note_form)
        return self.form_invalid(communication_form, note_form)


add_communication = test(NewPatientCommunicationFormView.as_view())


class GetCommunicationMixin(GetPatientMixin):
    def get_communication(self):
        if not hasattr(self, '_communication'):
            patient = self.get_patient()
            self._communication = patient.communications.get(
                pk=self.kwargs['communication_id'])
        return self._communication


class EditCommunicationFormView(GenesisFormView, GetCommunicationMixin):
    form_class = PatientCommunicationNoteForm
    go_back_until = ['accounts:patient-communications',
                     'accounts:communications']
    success_message = 'The communication has been updated.'
    template_name = 'accounts/patients/edit_patient_communication.html'
    prefix = 'note'

    def _get_breadcrumbs(self):
        return get_communication_breadcrumbs(
            self.get_communication(), self.request.user)

    def get_context_data(self, **kwargs):
        communication = self.get_communication()
        kwargs['previous_notes'] = communication.notes.order_by(
            'datetime_added')
        kwargs['patient'] = self.get_patient()
        kwargs['communication'] = communication
        return super(EditCommunicationFormView, self).get_context_data(
            **kwargs)

    def get_form_kwargs(self):
        kwargs = super(EditCommunicationFormView, self).get_form_kwargs()
        kwargs['requester'] = self.request.user
        kwargs['communication'] = self.get_communication()
        return kwargs

    def _get_page_title(self):
        return 'Edit Communication for {0}'.format(
            self.get_patient().get_reversed_name())

    def get_success_url(self, form):
        should_show_complaint = bool(filter(
            lambda x: x.is_device,
            form.cleaned_data['replacements']
        ))
        if should_show_complaint:
            patient = self.get_patient()
            device = patient.patient_profile.get_device()
            if device:
                complaints = device.complaints.order_by('-datetime_added')
                if complaints.count() > 0:
                    return reverse(
                        'gdrives:edit-complaint',
                        args=[device.pk, complaints[0].pk]
                    )
                return reverse('gdrives:new-complaint', args=[device.pk])


edit_communication = test(EditCommunicationFormView.as_view())


class CommunicationReportView(ReportView, GetCommunicationMixin):
    template_name = 'accounts/reports/communication.html'
    filename = 'communication.pdf'
    response_class = PDFPrintURLResponse

    def get_context_data(self, **kwargs):
        kwargs['communication'] = self.get_communication()
        kwargs['notes'] = self.get_communication().notes.order_by(
            'datetime_added')
        kwargs['requester'] = self.request.user
        return super(CommunicationReportView, self).get_context_data(
            **kwargs)


communication_pdf = user_passes_test(admin_user)(
    CommunicationReportView.as_view(output_format='pdf'))
communication_pdf_html = user_passes_test(admin_user)(
    CommunicationReportView.as_view(output_format='html'))


class PatientOrdersView(GenesisTableView, GetPatientMixin):
    def get_above_table_items(self):
        patient = self.get_patient()
        above_table = [
            GenesisAboveTableButton(
                'Export History',
                reverse('orders:patient-order-report',
                        args=[patient.pk])),
            GenesisAboveTableButton(
                'Create Order',
                reverse('orders:create-for-patient', args=[patient.pk]))
        ]
        return above_table

    def get_breadcrumbs(self):
        return get_patient_breadcrumbs(self.get_patient(), self.request.user)

    def get_columns(self):
        return [
            AttributeTableColumn(
                'Datetime Added',
                'datetime_added',
                default_sort_direction='desc',
                default_sort=True),
            AttributeTableColumn(
                'Order Status',
                'get_order_status_display',
                proxy_field='order_status'),
            AttributeTableColumn(
                'Order Origin',
                'get_order_origin_display',
                proxy_field='order_origin'),
            ActionTableColumn(
                'Details',
                actions=[
                    ActionItem(
                        'Details',
                        GenesisTableLink(
                            'orders:details',
                            url_args=[GenesisTableLinkAttrArg('pk')]
                        )
                    )
                ]
            )
        ]

    def get_page_title(self):
        return "Manage Orders for {0}".format(
            self.get_patient().get_reversed_name())

    def get_queryset(self):
        return self.get_patient().orders.all()


orders = test(PatientOrdersView.as_view())


# TODO: Convert to new CSVReportView when merged
@user_passes_test(admin_user)
def call_log_report(request):
    return generic_form(
        request,
        form_class=CallLogReportForm,
        form_kwargs={'requester': request.user},
        page_title='Generate Call Log',
        system_message='Your report has been generated.',
        send_download_url=True)
