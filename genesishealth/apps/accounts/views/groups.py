from datetime import datetime, time, timedelta, date
from typing import Optional, Dict, Any, List

from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse
from django.db.models import Avg, DurationField, ExpressionWrapper, F, QuerySet
from django.http import HttpResponseNotFound
from django.shortcuts import render
from django.utils.timezone import get_default_timezone, now

from genesishealth.apps.accounts.breadcrumbs.groups import (
    get_group_breadcrumbs)
from genesishealth.apps.accounts.forms.companies import ConfigureGlucoseAverageReportForm
from genesishealth.apps.accounts.forms.groups import (
    GroupForm, ImportGroupsForm,
    ParticipationReportForm, NoncompliantReportForm,
    TargetRangeReportForm, ParticipationStatusReportForm,
    ConfigurePatientExportForm, ConfigureExportAccountReportForm,
    ConfigureAccountStatusReportForm, ConfigureReadingDelayReportForm,
    InactiveParticipationStatusReportForm)
from genesishealth.apps.accounts.models import GenesisGroup, Company
from genesishealth.apps.accounts.models.profile_patient import (
    PatientCommunication)
from genesishealth.apps.readings.models import GlucoseReading
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.class_views import (
    AttributeTableColumn, ActionTableColumn,
    ActionItem, GenesisBaseDetailPane, GenesisDetailView,
    GenesisTableLink, GenesisTableLinkAttrArg, GenesisAboveTableButton,
    GenesisTableView)
from genesishealth.apps.utils.class_views.csv_report import (
    CSVReport, CSVReportView)
from genesishealth.apps.utils.request import admin_user, check_user_type
from genesishealth.apps.utils.views import generic_form


class GenesisGroupTableView(GenesisTableView):
    def create_columns(self):
        return [
            AttributeTableColumn('Name', 'name', cell_class='main'),
            AttributeTableColumn('Type', 'get_group_type_display'),
            AttributeTableColumn('Contact', 'contact'),
            AttributeTableColumn(
                'Number of Patients',
                'get_patients.count',
                searchable=False),
            AttributeTableColumn(
                'Number of Professionals',
                'get_professionals.count',
                searchable=False),
            ActionTableColumn(
                'View',
                actions=[
                    ActionItem(
                        'Detail',
                        GenesisTableLink(
                            'accounts:manage-groups-detail',
                            url_args=[GenesisTableLinkAttrArg('pk')]),
                        required_user_types=['admin']
                    ),
                ]
            )
        ]

    def get_above_table_items(self):
        return [
            GenesisAboveTableButton(
                'Add Partner',
                reverse('accounts:manage-groups-create')),
            GenesisAboveTableButton(
                'Import Business Partners',
                reverse('accounts:manage-groups-import')),
        ]

    def get_page_title(self):
        return 'Manage Business Partners'

    def get_queryset(self):
        return GenesisGroup.objects.all()


test = user_passes_test(admin_user)
main = test(GenesisGroupTableView.as_view())


@user_passes_test(admin_user)
def reports(request, group_id):
    try:
        group = GenesisGroup.objects.get(pk=group_id)
    except GenesisGroup.DoesNotExist:
        return HttpResponseNotFound()
    ctx = {
        'group': group,
        'breadcrumbs': [
            Breadcrumb('Business Partners',
                       reverse('accounts:manage-groups')),
            Breadcrumb(
                'Business Partner: {0}'.format(group.name),
                reverse('accounts:manage-groups-detail',
                        args=[group.pk]))
        ]
    }
    return render(request, 'accounts/group_reports.html', ctx)


@user_passes_test(admin_user)
def add(request):
    breadcrumbs = [
        Breadcrumb('Business Partners',
                   reverse('accounts:manage-groups')),
    ]
    return generic_form(
        request,
        form_class=GroupForm,
        page_title='Add Business Partner',
        breadcrumbs=breadcrumbs,
        system_message='The business partner has been created.')


@user_passes_test(admin_user)
def import_group(request):
    breadcrumbs = [
        Breadcrumb('Business Partners',
                   reverse('accounts:manage-groups')),
    ]
    return generic_form(
        request,
        form_class=ImportGroupsForm,
        page_title='Import Business Partners',
        breadcrumbs=breadcrumbs,
        system_message='The business partners have been imported.')


@user_passes_test(admin_user)
def participation_report(request, group_id):
    group = GenesisGroup.objects.get(pk=group_id)
    breadcrumbs = [
        Breadcrumb('Business Partners',
                   reverse('accounts:manage-groups')),
        Breadcrumb(
            'Business Partner: {0}'.format(group.name),
            reverse('accounts:manage-groups-detail',
                    args=[group.pk])),
        Breadcrumb(
            'Reports',
            reverse('accounts:manage-groups-reports',
                    args=[group.pk]))
    ]
    return generic_form(
        request,
        form_class=ParticipationReportForm,
        form_kwargs={'group': group, 'user': request.user},
        page_title='Generate Participation Report for {0}'.format(
            group.name),
        system_message='Your report has been generated.',
        breadcrumbs=breadcrumbs,
        send_download_url=True)


@user_passes_test(admin_user)
def participation_status_report(request, group_id):
    group = GenesisGroup.objects.get(pk=group_id)
    breadcrumbs = [
        Breadcrumb('Business Partners',
                   reverse('accounts:manage-groups')),
        Breadcrumb(
            'Business Partner: {0}'.format(group.name),
            reverse('accounts:manage-groups-detail',
                    args=[group.pk])),
        Breadcrumb(
            'Reports',
            reverse('accounts:manage-groups-reports',
                    args=[group.pk]))
    ]
    return generic_form(
        request,
        form_class=ParticipationStatusReportForm,
        form_kwargs={'group': group, 'user': request.user},
        page_title='Generate Participation Status Report for {0}'.format(
            group.name),
        system_message='Your report has been generated.',
        breadcrumbs=breadcrumbs,
        send_download_url=True)


@user_passes_test(admin_user)
def inactive_participation_status_report(request, group_id):
    group = GenesisGroup.objects.get(pk=group_id)
    breadcrumbs = [
        Breadcrumb('Business Partners',
                   reverse('accounts:manage-groups')),
        Breadcrumb(
            'Business Partner: {0}'.format(group.name),
            reverse('accounts:manage-groups-detail',
                    args=[group.pk])),
        Breadcrumb(
            'Reports',
            reverse('accounts:manage-groups-reports',
                    args=[group.pk]))
    ]
    return generic_form(
        request,
        form_class=InactiveParticipationStatusReportForm,
        form_kwargs={'group': group, 'user': request.user},
        page_title='Generate Inactive Participation Status Report for'
                   ' {0}'.format(group.name),
        system_message='Your report has been generated.',
        breadcrumbs=breadcrumbs,
        send_download_url=True)


@user_passes_test(admin_user)
def noncompliant_report(request, group_id):
    group = GenesisGroup.objects.get(pk=group_id)
    breadcrumbs = [
        Breadcrumb('Business Partners',
                   reverse('accounts:manage-groups')),
        Breadcrumb(
            'Business Partner: {0}'.format(group.name),
            reverse('accounts:manage-groups-detail',
                    args=[group.pk])),
        Breadcrumb(
            'Reports',
            reverse('accounts:manage-groups-reports',
                    args=[group.pk]))
    ]
    return generic_form(
        request,
        form_class=NoncompliantReportForm,
        form_kwargs={'group': group, 'user': request.user},
        page_title='Generate Noncompliant Report for {0}'.format(
            group.name),
        system_message='Your report has been generated.',
        breadcrumbs=breadcrumbs,
        send_download_url=True)


@user_passes_test(admin_user)
def target_range_report(request, group_id):
    group = GenesisGroup.objects.get(pk=group_id)
    breadcrumbs = [
        Breadcrumb('Business Partners',
                   reverse('accounts:manage-groups')),
        Breadcrumb(
            'Business Partner: {0}'.format(group.name),
            reverse('accounts:manage-groups-detail',
                    args=[group.pk])),
        Breadcrumb(
            'Reports',
            reverse('accounts:manage-groups-reports',
                    args=[group.pk]))
    ]
    return generic_form(
        request,
        form_class=TargetRangeReportForm,
        form_kwargs={'group': group, 'user': request.user},
        page_title='Generate Target Range Report for {0}'.format(
            group.name),
        system_message='Your report has been generated.',
        breadcrumbs=breadcrumbs,
        send_download_url=True)


@user_passes_test(lambda u: check_user_type(u, ['Admin', 'Professional']))
def edit(request, group_id=None):
    if group_id:
        if not request.user.is_admin():
            return HttpResponseNotFound()
        group = GenesisGroup.objects.get(pk=group_id)
        breadcrumbs = [
            Breadcrumb('Business Partners',
                       reverse('accounts:manage-groups')),
            Breadcrumb(
                'Business Partner: {0}'.format(group.name),
                reverse('accounts:manage-groups-detail',
                        args=[group.pk]))
        ]
    else:
        if not request.user.is_professional():
            return HttpResponseNotFound()
        breadcrumbs = []
        group = request.user.professional_profile.parent_group

    return generic_form(
        request,
        form_class=GroupForm,
        page_title='Edit %s' % group,
        thanks_view_name=(
            request.user.is_professional() and 'accounts:manage-my-group' or
            None),
        system_message='Business partner information has been updated.',
        breadcrumbs=breadcrumbs,
        form_kwargs={'instance': group})


class GroupInformationPane(GenesisBaseDetailPane):
    template_name = 'accounts/groups/detail_panes/information.html'
    pane_title = "Information"


class GroupShippingPane(GenesisBaseDetailPane):
    template_name = 'accounts/groups/detail_panes/shipping.html'
    pane_title = "Shipping Snapshot"


class GroupSnapshotPane(GenesisBaseDetailPane):
    template_name = 'accounts/groups/detail_panes/snapshot.html'
    pane_title = "People Snapshot"


class GroupGlucoseStatisticPane(GenesisBaseDetailPane):
    template_name = 'accounts/groups/detail_panes/glucose.html'
    pane_title = "Glucose Statistics"


class GroupDetailView(GenesisDetailView):
    pane_classes = (
        GroupInformationPane, GroupShippingPane, GroupSnapshotPane,
        GroupGlucoseStatisticPane)

    def __init__(self, *args, **kwargs):
        super(GroupDetailView, self).__init__(*args, **kwargs)
        self._group = None

    def get_breadcrumbs(self):
        return [
            Breadcrumb('Business Partners', reverse('accounts:manage-groups'))
        ]

    def get_buttons(self):
        group = self.get_group()
        if group.is_no_pii:
            return [
                GenesisAboveTableButton(
                    'Devices',
                    reverse('accounts:manage-groups-devices',
                            args=[group.id])),
                GenesisAboveTableButton(
                    'Communications',
                    reverse('accounts:groups-communications',
                            args=[group.id])),
                GenesisAboveTableButton(
                    'Reports',
                    reverse('accounts:manage-groups-reports',
                            args=[group.id])),
                GenesisAboveTableButton(
                    'Companies',
                    reverse('accounts:manage-groups-companies',
                            args=[group.id])),
                GenesisAboveTableButton(
                    'Patients',
                    reverse('accounts:manage-groups-patients',
                            args=[group.id])),
                GenesisAboveTableButton(
                    'Account Detail',
                    reverse('accounts:manage-groups-edit',
                            args=[group.id]))

            ]
        return [
            GenesisAboveTableButton(
                'Devices',
                reverse('accounts:manage-groups-devices',
                        args=[group.id])),
            GenesisAboveTableButton(
                'Communications',
                reverse('accounts:groups-communications',
                        args=[group.id])),
            GenesisAboveTableButton(
                'Demo Patients',
                reverse('accounts:manage-groups-demo',
                        args=[group.id])),
            GenesisAboveTableButton(
                'Reports',
                reverse('accounts:manage-groups-reports',
                        args=[group.id])),
            GenesisAboveTableButton(
                'Payors',
                reverse('accounts:manage-groups-payors',
                        args=[group.id])),
            GenesisAboveTableButton(
                'Companies',
                reverse('accounts:manage-groups-companies',
                        args=[group.id])),
            GenesisAboveTableButton(
                'Patients',
                reverse('accounts:manage-groups-patients',
                        args=[group.id])),
            GenesisAboveTableButton(
                'Professionals',
                reverse('accounts:manage-groups-professionals',
                        args=[group.id])),
            GenesisAboveTableButton(
                'Account Detail',
                reverse('accounts:manage-groups-edit',
                        args=[group.id]))

        ]

    def get_group(self):
        if self._group is None:
            self._group = GenesisGroup.objects.get(pk=self.kwargs['group_id'])
        return self._group

    def get_page_title(self):
        return 'Manage Business Partner {0}'.format(self.get_group())

    def get_pane_context(self):
        group = self.get_group()
        av = group.get_patients().aggregate(
            ave=Avg('patient_profile__stats__readings_last_90'))['ave']
        return {
            'group': group,
            'readings_per_day': av
        }


group_detail = test(GroupDetailView.as_view())


class GetGroupMixin(object):
    def get_group(self):
        if not hasattr(self, '_group'):
            self._group = GenesisGroup.objects.get(pk=self.kwargs['group_id'])
        return self._group


class GroupCommunicationsTableView(GenesisTableView, GetGroupMixin):
    extra_search_fields = ['patient__first_name']

    def create_columns(self):
        return [
            AttributeTableColumn(
                'Datetime Added',
                'datetime_added',
                default_sort_direction='desc',
                default_sort=True),
            AttributeTableColumn(
                'Added By',
                'added_by.get_reversed_name',
                proxy_field='added_by.last_name',
                searchable=False),
            AttributeTableColumn(
                'Patient',
                'patient.get_reversed_name',
                proxy_field='patient.last_name'
            ),
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
                            url_args=[GenesisTableLinkAttrArg('patient.pk'),
                                      GenesisTableLinkAttrArg('pk')])
                    ),
                    ActionItem(
                        'Report',
                        GenesisTableLink(
                            'accounts:communication-report-pdf',
                            url_args=[GenesisTableLinkAttrArg('patient.pk'),
                                      GenesisTableLinkAttrArg('pk')],
                            prefix='')
                    )
                ]
            )
        ]

    def get_above_table_items(self):
        group = self.get_group()
        above_table = []
        if self.should_show_closed():
            above_table.append(
                GenesisAboveTableButton(
                    'Show Open',
                    reverse('accounts:groups-communications',
                            args=[group.pk])
                ))
        else:
            above_table.append(
                GenesisAboveTableButton(
                    'Show Closed',
                    reverse('accounts:groups-communications',
                            args=[group.pk]) + "?show_closed=1"
                ))
        return above_table

    def get_breadcrumbs(self):
        return get_group_breadcrumbs(self.get_group(), self.request.user)

    def get_page_title(self):
        return 'Communications for {0}'.format(
            self.get_group().name)

    def get_queryset(self):
        qs = PatientCommunication.objects.filter(
            patient__patient_profile__group=self.get_group())
        if self.should_show_closed():
            return qs.filter(status__is_closed=True)
        return qs.filter(status__is_closed=False)

    def should_show_closed(self):
        return self.request.GET.get('show_closed', 0) == '1'


communications = test(GroupCommunicationsTableView.as_view())


class GroupExportReport(CSVReport):
    configuration_form_class = ConfigurePatientExportForm

    header_rows = [[
        "Patient ID",
        "Insurance Identifier",
        "Username",
        "First Name",
        "Middle Initial",
        "Last Name",
        "Email",
        "Timezone",
        "Date of Birth",
        "Gender",
        "Address",
        "City",
        "State",
        "ZIP",
        "Phone",
        "Cell Phone",
        "Preferred Contact Method",
        "MEID",
        "Alerts"
    ]]

    def _configure(self, **kwargs):
        self.business_partner = GenesisGroup.objects.get(
            pk=kwargs['business_partner_id'])
        self.user = User.objects.get(pk=kwargs['user_id'])

    def get_configuration_form_kwargs(self):
        kwargs = super(GroupExportReport, self).get_configuration_form_kwargs()
        kwargs['group'] = self.business_partner
        kwargs['user'] = self.user
        return kwargs

    def get_filename(self, data):
        return "{0}_{1}_patients.csv".format(
            now().date().strftime("%Y%m%d"),
            self.business_partner.name)

    def get_header_rows(self, data):
        rows = super(GroupExportReport, self).get_header_rows(data)
        top_rows = [
            ['Title', 'Patient Report'],
            ['Date', now().date().strftime("%m/%d/%Y")],
            ['Business Partner', self.business_partner.name],
            ['Number of Patients', self.get_queryset(data).count()],
            []
        ]
        rows = top_rows + rows
        return rows

    def get_item_row(self, patient):
        profile = patient.patient_profile
        contact = profile.contact
        device = profile.get_device()
        if device is None:
            meid = "N/A"
        else:
            meid = device.meid

        return [
            patient.pk,
            profile.insurance_identifier,
            patient.username,
            patient.first_name,
            contact.middle_initial,
            patient.last_name,
            patient.email,
            profile.timezone_name,
            profile.date_of_birth,
            profile.gender,
            contact.address1,
            contact.city,
            contact.state,
            contact.zip,
            contact.phone,
            contact.cell_phone,
            profile.preferred_contact_method,
            meid,
            ""
        ]

    def get_queryset(self, data):
        if not hasattr(self, '_qs'):
            tz = get_default_timezone()
            patients = self.business_partner.get_patients()
            if data['account_filter'] == 'today':
                start = now()
                end = now() + timedelta(days=1) - timedelta(microseconds=1)
                patients = patients.filter(date_joined__range=(start, end))
            elif data['account_filter'] == 'custom':
                start = tz.localize(
                    datetime.combine(data['report_start'], time()))
                end = tz.localize(
                    datetime.combine(data['report_end'], time()))
                patients = patients.filter(date_joined__range=(start, end))
            self._qs = patients
        return self._qs


class GroupExportReportView(CSVReportView, GetGroupMixin):
    page_title = "Export Patients - Old Format"
    success_message = "Your report has been generated."
    report_class = GroupExportReport

    def _get_breadcrumbs(self):
        group = self.get_group()
        return [
            Breadcrumb('Business Partners',
                       reverse('accounts:manage-groups')),
            Breadcrumb(
                'Business Partner: {0}'.format(group.name),
                reverse('accounts:manage-groups-detail',
                        args=[group.pk])),
            Breadcrumb(
                'Reports',
                reverse('accounts:manage-groups-reports',
                        args=[group.pk]))
        ]

    def _get_report_kwargs(self):
        return {
            'business_partner_id': self.get_group().id,
            'user_id': self.request.user.id
        }


group_export = test(GroupExportReportView.as_view())


class GroupExportAccountReport(CSVReport):
    configuration_form_class = ConfigureExportAccountReportForm

    def _configure(self, **kwargs):
        self.business_partner = GenesisGroup.objects.get(
            pk=kwargs['business_partner_id'])
        self.user = User.objects.get(pk=kwargs['user_id'])

    def get_configuration_form_kwargs(self):
        kwargs = super(GroupExportAccountReport, self)\
            .get_configuration_form_kwargs()
        kwargs['group'] = self.business_partner
        kwargs['user'] = self.user
        return kwargs

    def get_filename(self, data):
        return "{0}_{1}_account_numbers.csv".format(
            now().date().strftime("%Y%m%d"),
            data['company'].name)

    def get_header_rows(self, data):
        top_rows = [
            ['Title', 'Genesis Account No'],
            ['Date', now().date().strftime("%m/%d/%Y")],
            ['Business Partner', data['company'].name],
            ['Number of Patients', self.get_queryset(data).count()],
            []
        ]
        if self.business_partner.is_no_pii:
            rows = [[
                "EPC_ID",
                "GHT_ACCOUNT_NO",
                "CREATED_ON",
                "ACTION"
            ]]
        else:
            rows = [[
                "FIRSTNAME",
                "INITIAL",
                "LASTNAME",
                "GENDER",
                "DOB",
                "EMAIL",
                "ADDRESS1",
                "ADDRESS2",
                "CITY",
                "STATE",
                "ZIPCODE",
                "PHONE",
                "INSURANCEID",
                "INSURANCEIDSUFFIX",
                "ACTION",
                "GHT_ACCOUNT_NO",
                "CREATED_ON",
                "EPC_MEMBER_ID"
            ]]
        rows = top_rows + rows
        return rows

    def get_item_row(self, patient):
        profile = patient.patient_profile
        contact = profile.contact
        dtformat = "%m/%d/%Y"
        if profile.date_of_birth:
            dob = profile.date_of_birth.strftime(dtformat)
        else:
            dob = ""
        if self.business_partner.is_no_pii:
            return [
                profile.epc_member_identifier,
                patient.id,
                patient.date_joined.strftime(dtformat),
                "ACCOUNT"
            ]
        return [
            patient.first_name,
            "",
            patient.last_name,
            profile.gender,
            dob,
            patient.email,
            contact.address1,
            contact.address2,
            contact.city,
            contact.state,
            contact.zip,
            contact.phone,
            profile.insurance_identifier,
            "",
            "ACCOUNT",
            patient.id,
            patient.date_joined.strftime(dtformat),
            profile.epc_member_identifier
        ]

    def get_queryset(self, data):
        if not hasattr(self, '_qs'):
            tz = get_default_timezone()
            patients = self.business_partner.get_patients().filter(
                patient_profile__company=data['company'])
            if data['account_filter'] == 'today':
                dt = tz.localize(datetime.combine(now().date(), time()))
                end = dt + timedelta(days=1) - timedelta(microseconds=1)
                patients = patients.filter(date_joined__range=(dt, end))
            elif data['account_filter'] == 'custom':
                start = tz.localize(
                    datetime.combine(data['report_start'], time()))
                end = tz.localize(
                    datetime.combine(
                        data['report_end'],
                        time()
                    ) + timedelta(days=1) - timedelta(microseconds=1))
                patients = patients.filter(
                    date_joined__range=(start, end))
            self._qs = patients
        return self._qs


class GroupExportAccountReportView(CSVReportView, GetGroupMixin):
    page_title = "Export Account Number File"
    success_message = "Your report has been generated."
    report_class = GroupExportAccountReport

    def _get_breadcrumbs(self):
        group = self.get_group()
        return [
            Breadcrumb('Business Partners',
                       reverse('accounts:manage-groups')),
            Breadcrumb(
                'Business Partner: {0}'.format(group.name),
                reverse('accounts:manage-groups-detail',
                        args=[group.pk])),
            Breadcrumb(
                'Reports',
                reverse('accounts:manage-groups-reports',
                        args=[group.pk]))
        ]

    def _get_report_kwargs(self):
        return {
            'business_partner_id': self.get_group().id,
            'user_id': self.request.user.id
        }


group_export_accounts = test(GroupExportAccountReportView.as_view())


class GroupAccountStatusReport(CSVReport):
    configuration_form_class = ConfigureAccountStatusReportForm

    def _configure(self, **kwargs):
        self.business_partner = GenesisGroup.objects.get(
            pk=kwargs['business_partner_id'])
        self.user = User.objects.get(pk=kwargs['user_id'])

    def get_configuration_form_kwargs(self):
        kwargs = super(GroupAccountStatusReport, self)\
            .get_configuration_form_kwargs()
        kwargs['group'] = self.business_partner
        kwargs['user'] = self.user
        return kwargs

    def get_filename(self, data):
        return "{0}_{1}_account_status.csv".format(
            now().date().strftime("%Y%m%d"),
            data['company'].name)

    def get_header_rows(self, data):
        top_rows = [
            ['Title', 'Genesis Account No'],
            ['Date', now().date().strftime("%m/%d/%Y")],
            ['Group', data['company'].name],
            ['Number of Patients', self.get_queryset(data).count()],
            []
        ]
        if self.business_partner.is_no_pii:
            rows = [[
                'EPC_ID',
                'GHT_ACCOUNT_NO',
                'STATUS',
                'INACTIVEDATE',
                'MEID'
            ]]
        else:
            rows = [[
                "FIRSTNAME",
                "INITIAL",
                "LASTNAME",
                "GENDER",
                "DOB",
                "EMAIL",
                "ADDRESS1",
                "ADDRESS2",
                "CITY",
                "STATE",
                "ZIPCODE",
                "PHONE",
                "INSURANCEID",
                "STATUS",
                "INACTIVEDATE",
                "MEID",
                "EPC_MEMBER_ID",
                "GHT_ACCOUNT_NO"
            ]]
        rows = top_rows + rows
        return rows

    def get_item_row(self, patient):
        profile = patient.patient_profile
        contact = profile.contact
        dtformat = "%m/%d/%Y"
        device = profile.get_device()
        if profile.date_of_birth:
            dob = profile.date_of_birth.strftime(dtformat)
        else:
            dob = ""
        if self.business_partner.is_no_pii:
            return [
                profile.epc_member_identifier,
                patient.id,
                profile.get_account_status_display(),
                profile.account_termination_date,
                device.meid if device else "N/A",
            ]
        return [
            patient.first_name,
            "",
            patient.last_name,
            profile.gender,
            dob,
            patient.email,
            contact.address1,
            contact.address2,
            contact.city,
            contact.state,
            contact.zip,
            contact.phone,
            profile.insurance_identifier,
            profile.get_account_status_display(),
            profile.account_termination_date,
            device.meid if device else "N/A",
            profile.epc_member_identifier,
            patient.id
        ]

    def get_queryset(self, data):
        if not hasattr(self, '_qs'):
            patients = self.business_partner.get_patients().filter(
                patient_profile__company=data['company'])
            if (data['account_filter'] !=
                    ConfigureAccountStatusReportForm.ACCOUNT_FILTER_ALL):
                patients = patients.filter(
                    patient_profile__account_status=data['account_filter'])
            self._qs = patients
        return self._qs


class GroupAccountStatusReportView(CSVReportView, GetGroupMixin):
    page_title = "Export Account Status File"
    success_message = "Your report has been generated."
    report_class = GroupAccountStatusReport

    def _get_breadcrumbs(self):
        group = self.get_group()
        return [
            Breadcrumb('Business Partners',
                       reverse('accounts:manage-groups')),
            Breadcrumb(
                'Business Partner: {0}'.format(group.name),
                reverse('accounts:manage-groups-detail',
                        args=[group.pk])),
            Breadcrumb(
                'Reports',
                reverse('accounts:manage-groups-reports',
                        args=[group.pk]))
        ]

    def _get_report_kwargs(self):
        return {
            'business_partner_id': self.get_group().id,
            'user_id': self.request.user.id
        }


group_account_status = test(GroupAccountStatusReportView.as_view())


class GroupReadingDelayReport(CSVReport):
    configuration_form_class = ConfigureReadingDelayReportForm

    header_rows = [[
        "Company",
        "GHT ID",
        "Insurance ID",
        "MEID",
        "Glucose Value",
        "Device Timestamp",
        "Server Timestamp (Received)"
        "Lag Time",
        "Bucket"
    ]]

    def _configure(self, **kwargs):
        self.business_partner = GenesisGroup.objects.get(
            pk=kwargs['business_partner_id'])
        self.user = User.objects.get(pk=kwargs['user_id'])

    def get_configuration_form_kwargs(self):
        kwargs = super(GroupReadingDelayReport, self)\
            .get_configuration_form_kwargs()
        kwargs['group'] = self.business_partner
        kwargs['user'] = self.user
        return kwargs

    def get_filename(self, data):
        return "{0}_{1}_{2}_delayed_reading.csv".format(
            data['start_date'].strftime("%Y_%m_%d"),
            data['end_date'].strftime("%Y_%m_%d"),
            self.business_partner.name)

    def get_header_rows(self, data):
        headers = super(GroupReadingDelayReport, self).get_header_rows(data)
        return [
            ['Title', 'Delayed Reading Report'],
            ['Date Range', "{0} - {1}".format(
                data['start_date'].strftime("%m/%d/%Y"),
                data['end_date'].strftime('%m/%d/%Y'))],
            []
        ] + headers

    def get_item_row(self, reading):
        profile = reading.patient.patient_profile
        user = profile.user
        log_entry = reading.gdrive_log_entry

        lag_days = reading.lag_time.days
        lag_hours = reading.lag_time.seconds / 60 / 60
        lag_minutes = reading.lag_time.seconds % 3600 / 60
        lag_seconds = reading.lag_time.seconds % 60

        if lag_days > 0:
            lag_string = "{0} {1}:{2}:{3}".format(
                lag_days,
                lag_hours,
                lag_minutes,
                lag_seconds
            )
        else:
            lag_string = "{0}:{1}:{2}".format(
                lag_hours,
                lag_minutes,
                lag_seconds
            )

        if lag_days > 0:
            bucket = '> 24h'
        elif reading.lag_time.seconds > (60 * 60):
            bucket = '1h - 24h'
        elif reading.lag_time.seconds > (60 * 5):
            bucket = '5m - 60m'
        elif reading.lag_time.seconds > (60 * 3):
            bucket = '3m - 5m'
        elif reading.lag_time.seconds > 60:
            bucket = '1m - 3m'
        else:
            bucket = '< 1m'

        return [
            profile.company.name,
            user.id,
            profile.insurance_identifier,
            reading.device.meid if reading.device is not None else "N/A",
            reading.glucose_value,
            str(reading.reading_datetime_utc),
            str(log_entry.date_created),
            lag_string,
            bucket
        ]

    def get_queryset(self, data):
        if not hasattr(self, '_qs'):
            expression = ExpressionWrapper(
                F('gdrive_log_entry__date_created') -
                F('reading_datetime_utc'),
                DurationField())
            tz = get_default_timezone()
            start = tz.localize(
                datetime.combine(data['start_date'], time()))
            end = tz.localize(
                datetime.combine(data['end_date'], time()))
            readings = GlucoseReading.objects.filter(
                reading_datetime_utc__range=(start, end),
                patient__patient_profile__company__in=data['companies']
            ).annotate(lag_time=expression)
            self._qs = readings
        return self._qs


class GroupReadingDelayReportView(CSVReportView, GetGroupMixin):
    page_title = "Export Reading Delay Report"
    success_message = "Your report has been generated."
    report_class = GroupReadingDelayReport

    def _get_breadcrumbs(self):
        group = self.get_group()
        return [
            Breadcrumb('Business Partners',
                       reverse('accounts:manage-groups')),
            Breadcrumb(
                'Business Partner: {0}'.format(group.name),
                reverse('accounts:manage-groups-detail',
                        args=[group.pk])),
            Breadcrumb(
                'Reports',
                reverse('accounts:manage-groups-reports',
                        args=[group.pk]))
        ]

    def _get_report_kwargs(self):
        return {
            'business_partner_id': self.get_group().id,
            'user_id': self.request.user.id
        }


group_reading_delay_report = test(GroupReadingDelayReportView.as_view())


class GlucoseAverageCSVReport(CSVReport):
    configuration_form_class = ConfigureGlucoseAverageReportForm

    _group: GenesisGroup
    _company: Optional[Company]
    _user: User
    _qs: 'QuerySet[User]'

    __glucose_averages: Dict[User, float]

    def _configure(self, **kwargs: Any) -> None:
        self._group = GenesisGroup.objects.get(pk=kwargs['group_id'])
        if 'company_id' in kwargs:
            self._company = self._group.companies.get(pk=kwargs['company_id'])
        else:
            self._company = None
        self._user = User.objects.get(pk=kwargs['user_id'])

    def get_configuration_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_configuration_form_kwargs()
        kwargs['group'] = self._group
        kwargs['user'] = self._user
        return kwargs

    def get_filename(self, data: Dict[str, Any]) -> str:
        report_name: str
        if self._company is not None:
            report_name = self._company.name
        else:
            report_name = self._group.name
        report_name = report_name.lower().replace(' ', '_')
        return "{0}_{1}_{2}_average_glucose.csv".format(
            data['start_date'].strftime("%Y_%m_%d"),
            data['end_date'].strftime("%Y_%m_%d"),
            report_name)

    def get_header_rows(self, data: Dict[str, Any]) -> List[List[str]]:
        queryset = self.get_queryset(data)
        all_averages = list(filter(
            lambda x: x is not None,
            self.__calculate_averages(
                queryset, data['start_date'], data['end_date']
            ).values()
        ))
        avg: str
        if len(all_averages) == 0:
            avg = 'N/A'
        else:
            avg = str(sum(all_averages) / len(all_averages))
        return [
            ['First Name', 'Last Name', 'Insurance ID', 'Avg Blood Glucose Reading'],
            ['GROUP', 'AVERAGE', '', avg]
        ]

    def get_item_row(self, patient: User) -> List[str]:
        qs = self.get_queryset({})
        avg = self.__calculate_averages(qs, None, None)
        return [
            patient.first_name,
            patient.last_name,
            patient.patient_profile.insurance_identifier or 'N/A',
            str(avg[patient])
        ]

    def get_queryset(self, data) -> 'QuerySet[User]':
        if not hasattr(self, '_qs'):
            if self._company is not None:
                self._qs = User.objects.filter(patient_profile__company=self._company)
            else:
                self._qs = User.objects.filter(patient_profile__group=self._group)
        return self._qs

    def __calculate_averages(self, qs: 'QuerySet[User]', start_date: date, end_date: date) -> Dict[User, float]:
        if not hasattr(self, '_glucose_averages'):
            output: Dict[User, float] = {}
            for patient in qs:
                readings = patient.glucose_readings.filter(
                    reading_datetime_utc__range=(start_date, end_date + timedelta(days=1))
                )
                avg = readings.aggregate(reading_avg=Avg('glucose_value'))['reading_avg']
                output[patient] = avg
            self._glucose_averages = output
        return self._glucose_averages


class GlucoseAverageCSVReportView(CSVReportView, GetGroupMixin):
    page_title = "Export Glucose Average View"
    success_message = "Your report has been generated."
    report_class = GlucoseAverageCSVReport

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
                'Reports',
                reverse('accounts:manage-groups-reports',
                        args=[group.pk]))
        ]

    def _get_report_kwargs(self) -> Dict[str, Any]:
        return {
            'group_id': self.get_group().id,
            'user_id': self.request.user.id
        }


glucose_average_report_view = test(GlucoseAverageCSVReportView.as_view())
