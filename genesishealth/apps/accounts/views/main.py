from datetime import date, datetime, time, timedelta
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from functools import reduce
from urllib.parse import urlencode

from django.db.models import Count
from django.http import HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import views
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.timezone import get_default_timezone, now
from django.views.generic import TemplateView

from genesishealth.apps.accounts.forms.main import (
    ResetPasswordEmailForm, ResetPasswordPhoneForm, ResetPasswordForm,
    ConfigureForm, SecurityQuestionsForm, UpdateEmailForm, UpdatePasswordForm,
    ResetPasswordEmailFinishForm, AdminChangeUsernameForm,
    AdminCheckSecurityQuestionForm, AdminChangePasswordForm,
    PhonelessConfigureForm, AdminSetDefaultPasswordForm,
    PickStartEndMonthForm)
from genesishealth.apps.accounts.forms.patients import PatientMyProfileForm
from genesishealth.apps.accounts.forms.professionals import (
    ProfessionalMyProfileForm)
from genesishealth.apps.accounts.forms.retrieve_username import (
    UserInfoVerificationForm, VerifySecurityQuestionForm)
from genesishealth.apps.accounts.models import (
    PatientProfile, ProfessionalProfile)
from genesishealth.apps.accounts.models.profile_patient import (
    PatientCommunication, PatientCommunicationNote)
from genesishealth.apps.accounts.password import make_password
from genesishealth.apps.dropdowns.models import CommunicationCategory
from genesishealth.apps.reports.views.main import (
    ReportView, PDFPrintURLResponse)
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.class_views import (
    AttributeTableColumn, ActionTableColumn,
    ActionItem, GenesisTableLink, GenesisTableLinkAttrArg,
    GenesisTableView, GenesisAboveTableButton, GenesisFormView)
from genesishealth.apps.utils.func import utcnow, get_home_view_name
from genesishealth.apps.utils.request import (
    admin_user, check_user_type, redirect_with_message, debug_response,
    genesis_redirect)
from genesishealth.apps.utils.views import generic_form


prof_and_patient = user_passes_test(
    lambda u: check_user_type(u, ['Patient', 'Professional']))


def lost_password(request):  # REFACTOR
    forms = [ResetPasswordEmailForm, ResetPasswordPhoneForm]
    # We keep track of the step we're in the form, using the session
    # The steps are 0-based, so that they can be used as list indices
    step = request.session.get('lp_step', 0)
    print(step)

    if request.method == "POST":
        form = forms[step](request.POST)
        if form.is_valid():
            # If we're in step 0 and the username is not a valid email,
            # we retrieve the user and move to the next step
            if step == 0 and '@' not in form.cleaned_data['username']:
                user = User.objects.get(username=form.cleaned_data['username'])

                # The form is initialed and falls through
                form = forms[step + 1](user=user)
                request.session['lp_step'] = step + 1
            else:
                form.save()

                # If the form is valid, we reset the step
                request.session['lp_step'] = 0

                if '@' in form.cleaned_data['username']:
                    context = {'form': form, 'contact': 'email'}
                else:
                    context = {'form': form, 'contact': 'phone'}
                return render(
                    request,
                    "accounts/lost_password/thanks.html",
                    context)
        else:
            # If there are non_field_errors, it means something or someone
            # tampered with the hidden fields, so we must restart the process
            if form.non_field_errors():
                request.session['lp_step'] = 0
    else:
        # Only the `ResetPasswordEmailForm` can be displayed on a normal GET
        # request. `ResetPasswordPhoneForm` should always be displayed after a
        # POST request that sets the username and its hidden associated data
        form = forms[0]()
        request.session['lp_step'] = 0

    return render(request, "accounts/lost_password.html", {"form": form})


class RetrieveUsernameView(TemplateView):  # REFACTOR
    template_name = 'accounts/retrieve_username.html'
    title = 'Information Verification Page'

    def get_context_data(self, **kwargs):
        kwargs['title'] = self.title
        return kwargs

    def get(self, request, *args, **kwargs):
        form = UserInfoVerificationForm()
        return self.render_to_response(self.get_context_data(form=form))

    def post(self, request, *args, **kwargs):
        hidden_data = {}
        form_kwargs = {'data': request.POST}
        form = UserInfoVerificationForm(**form_kwargs)
        if form.is_valid():
            user = form.user

            hidden_data = form.cleaned_data.copy()
            if form.cleaned_data.get('date_of_birth'):
                hidden_data['date_of_birth_day'] = form.cleaned_data[
                    'date_of_birth'].day
                hidden_data['date_of_birth_month'] = form.cleaned_data[
                    'date_of_birth'].month
                hidden_data['date_of_birth_year'] = form.cleaned_data[
                    'date_of_birth'].year
                del hidden_data['date_of_birth']

            submitted = any([
                True for k, v in request.POST.iteritems()
                if k.startswith('f2-')])
            if not submitted:
                del form_kwargs['data']

            if user.get_profile().configured:
                form = VerifySecurityQuestionForm(
                    prefix='f2', user=user, **form_kwargs)
            else:
                self.title = 'Setup Security Questions'
                form = PhonelessConfigureForm(
                    prefix='f2', user=user, **form_kwargs)

            if submitted and form.is_valid():
                form.save()
                self.title = 'Verification successful'
                return self.render_to_response(
                    self.get_context_data(username=user.username))

        return self.render_to_response(
            self.get_context_data(form=form, hidden_data=hidden_data))
retrieve_username = RetrieveUsernameView.as_view()


@user_passes_test(lambda u: check_user_type(u, ['Patient', 'Professional']))
def my_profile(request):  # REFACTOR
    if request.user.is_patient():
        form_class = PatientMyProfileForm
        form_kwargs = {'patient': request.user}
    else:
        form_class = ProfessionalMyProfileForm
        form_kwargs = {'instance': request.user}

    return generic_form(request,
                        form_class=form_class,
                        page_title='Update Your Profile',
                        system_message='Your profile has been updated.',
                        go_back_until=(('accounts:profile',),),
                        form_kwargs=form_kwargs)


def custom_login(request, *args, **kwargs):
    response = views.LoginView.as_view(
        template_name='accounts/login.html')(request, *args, **kwargs)
    if isinstance(response, HttpResponseRedirect):
        try:
            profile = request.user.get_profile()
        except Exception:
            pass
        else:
            if request.user.is_patient() and profile.configured is False:
                return HttpResponseRedirect('#'.join([
                    reverse('dashboard:index'),
                    reverse('accounts:setup-security')]))
    return response


@user_passes_test(lambda u: check_user_type(u, ['Patient', 'Professional']))
def setup_security(request, **kwargs):  # REFACTOR
    return generic_form(
        request,
        form_class=ConfigureForm,
        form_kwargs={'user': request.user},
        page_title='Set up security questions',
        system_message='Your security questions have been updated.',
        thanks_view_name=reverse('dashboard:home'))


@user_passes_test(lambda u: check_user_type(u, ['Patient', 'Professional']))
def reset_password_finish(request, **kwargs):  # REFACTOR
    """This screen appears when the user logs in for the first time
    after having their password reset."""
    return generic_form(
        request,
        form_class=ResetPasswordEmailFinishForm,
        form_kwargs={'requester': request.user},
        page_title='Change your password',
        system_message='Your password has been updated.',
        thanks_view_name=reverse('dashboard:home'))


@login_required
def logout(request, **kwargs):  # REFACTOR - even needed?
    return views.LogoutView.as_view(
        template_name='accounts/logout.html')(request, **kwargs)


@user_passes_test(
    lambda u: check_user_type(u, ['Patient', 'Professional']))
def security_questions(request):  # REFACTOR
    return generic_form(
        request,
        form_class=SecurityQuestionsForm,
        form_kwargs={'user': request.user},
        page_title='Set up security questions',
        system_message='Your security questions have been updated.',
        thanks_view_name=reverse('dashboard:home'),
        extra_form_context={
            'form_message':
                'For security reasons, your answers are not displayed.'})


@user_passes_test(admin_user)
def manage_login(request, user_id):  # REFACTOR
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist as e:  # pragma: no cover
        return debug_response(e)

    form_classes = {
        'change_username': AdminChangeUsernameForm,
        'check_security_question': AdminCheckSecurityQuestionForm,
        'change_password': AdminChangePasswordForm,
        'set_default_password_form': AdminSetDefaultPasswordForm
    }
    forms = {}
    form_kwargs = {'instance': user}

    if request.method == 'POST':
        form_class = form_classes[request.POST['form_name']]
        form = form_class(request.POST, **form_kwargs)
        if form.is_valid():
            form.save()
            form_success_messages = {
                'change_username': 'The user\'s username has been updated.',
                'check_security_question':
                    'The user\'s security question has '
                    'been answered correctly.',
                'change_password': 'The user\'s password has been updated.',
                'set_default_password_form':
                    'The user\'s password has been updated.'
            }
            message = form_success_messages[request.POST['form_name']]
            return redirect_with_message(
                request, None, message,
                go_back_until=['accounts:manage-login'])
        forms[request.POST['form_name']] = form
        cj = filter(lambda x: x[1] != form_class, form_classes.items())
        for other_form_name, other_form_class in cj:
            forms[other_form_name] = other_form_class(**form_kwargs)
    else:
        for form_name, form_class in form_classes.items():
            forms[form_name] = form_class(**form_kwargs)
    if user.is_patient():
        group = user.patient_profile.get_group()
        if group:
            breadcrumbs = [
                Breadcrumb('Business Partners',
                           reverse('accounts:manage-groups')),
                Breadcrumb(
                    'Business Partner: {0}'.format(group.name),
                    reverse('accounts:manage-groups-detail',
                            args=[group.pk])),
                Breadcrumb(
                    'Patients'.format(group.name),
                    reverse('accounts:manage-groups-patients',
                            args=[group.pk]))
            ]
        else:
            breadcrumbs = [
                Breadcrumb('Users', reverse('accounts:manage-users'))]
        breadcrumbs.append(
            Breadcrumb(
                'Patient: {0}'.format(user.get_reversed_name()),
                reverse('accounts:manage-patients-detail', args=[user.pk])))
    else:
        group = user.professional_profile.parent_group
        breadcrumbs = [
            Breadcrumb('Business Partners',
                       reverse('accounts:manage-groups')),
            Breadcrumb(
                'Business Partner: {0}'.format(group.name),
                reverse('accounts:manage-groups-detail',
                        args=[group.pk])),
            Breadcrumb(
                'Professionals'.format(group.name),
                reverse('accounts:manage-groups-professionals',
                        args=[group.pk])),
            Breadcrumb(
                'Professional: {0}'.format(user.get_reversed_name()),
                reverse('accounts:manage-professionals-detail', args=[user.pk])
            )
        ]

    ctx = {
        'target_user': user,
        'forms': forms,
        'breadcrumbs': breadcrumbs,
        'new_password': make_password(user)
    }
    return render(
        request, 'accounts/manage_login.html', ctx)


@user_passes_test(admin_user)
def reset_password_confirm(request, user_id):  # REFACTOR
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:  # pragma: no cover
        return HttpResponseNotFound()

    user.get_profile().reset_password()

    return redirect_with_message(
        request, None, 'The user\'s password has been reset.')


@login_required
def update_password(request):  # REFACTOR
    try:
        user = request.user
    except User.DoesNotExist:  # pragma: no cover
        return HttpResponseNotFound()

    return generic_form(
        request,
        form_class=UpdatePasswordForm,
        form_kwargs={'user': user},
        page_title="Update your password",
        system_message="Your password has been updated.")


@login_required
def update_password_expired(request):  # REFACTOR
    user = request.user
    return generic_form(
        request,
        form_class=UpdatePasswordForm,
        form_kwargs={'user': user},
        page_title="Your password has expired",
        thanks_view_name=reverse(get_home_view_name(request.user)),
        system_message="Your password has been updated.")


@user_passes_test(
    lambda u: check_user_type(u, ['Patient', 'Professional', 'Admin']))
def update_email(request):  # REFACTOR
    return generic_form(
        request,
        form_class=UpdateEmailForm,
        form_kwargs={'user': request.user},
        page_title='Update Your Email Address',
        system_message='Your email address has been updated.',
        form_template='accounts/update_email.html')


def reset_password(request, forgot_hash):  # REFACTOR
    try:
        user = User.objects.get(
            patient_profile__forgot_key=forgot_hash,
            patient_profile__forgot_key_updated__gt=(
                utcnow() - timedelta(days=1)))
    except User.DoesNotExist:
        try:
            user = User.objects.get(
                professional_profile__forgot_key=forgot_hash,
                professional_profile__forgot_key_updated__gt=(
                    utcnow() - timedelta(days=1)))
        except User.DoesNotExist:
            return HttpResponseNotFound()

    if request.method == "POST":
        form = ResetPasswordForm(request.POST, user=user)
        if form.is_valid():
            user.set_password(form.cleaned_data["password"])
            user.forgot_key = None
            user.forgot_key_updated = None
            user.save()
            return HttpResponseRedirect('/accounts/reset/thanks/')
    else:
        form = ResetPasswordForm(user=user)
    return render(request, "accounts/reset.html", {"form": form})

admin_test = user_passes_test(admin_user)


class UserTableView(GenesisTableView):
    extra_search_fields = [
        'patient_profile__insurance_identifier',
        'patient_profile__epc_member_identifier',
        'gdrives__meid',
        'id']

    def create_columns(self):
        return [
            AttributeTableColumn(
                'Last Name', 'last_name', cell_class='main'),
            AttributeTableColumn(
                'First Name', 'first_name'),
            AttributeTableColumn(
                'Business Partner', 'get_profile.business_partner',
                failsafe='None', searchable=False, sortable=False),
            AttributeTableColumn(
                'Employer', 'get_profile.company',
                failsafe='None', searchable=False, sortable=False),
            AttributeTableColumn(
                'Date of Birth', 'get_profile.date_of_birth',
                searchable=False, sortable=False),
            AttributeTableColumn(
                'Address', 'get_profile.contact.address1',
                searchable=False, sortable=False),
            AttributeTableColumn(
                'City', 'get_profile.contact.city',
                searchable=False, sortable=False),
            AttributeTableColumn(
                'State', 'get_profile.contact.state',
                searchable=False, sortable=False),
            AttributeTableColumn(
                'Zip', 'get_profile.contact.zip',
                searchable=False, sortable=False),
            AttributeTableColumn(
                'Login Type', 'get_profile.login_type',
                searchable=False, sortable=False),
            ActionTableColumn(
                'View',
                actions=[
                    ActionItem(
                        'Details',
                        GenesisTableLink(
                            'accounts:manage-patients-detail',
                            url_args=[GenesisTableLinkAttrArg('pk')]),
                        condition=['is_patient']
                    ),
                    ActionItem(
                        'Details',
                        GenesisTableLink(
                            'accounts:manage-professionals-detail',
                            url_args=[GenesisTableLinkAttrArg('pk')]),
                        condition=['is_professional']
                    )
                ]
            )
        ]

    def get_page_title(self):
        return 'Manage Users'

    def get_queryset(self):
        return (
            PatientProfile.myghr_patients.get_users().filter(
                patient_profile__is_scalability_user=False).exclude(
                first_name='',
                last_name='',
                patient_profile__group__is_no_pii=False) |
            ProfessionalProfile.objects.get_users())


users = admin_test(UserTableView.as_view())


class AcceptSomethingView(TemplateView):
    target_field = None

    def post(self, request, *args, **kwargs):
        profile = self.request.user.get_profile()
        setattr(profile, self.target_field, True)
        profile.save()
        print(self.target_field)
        return genesis_redirect(request, reverse('dashboard:home'))

accept_terms = prof_and_patient(AcceptSomethingView.as_view(
    template_name='accounts/accept_terms.html',
    target_field='is_accepted_terms'))
accept_privacy = prof_and_patient(AcceptSomethingView.as_view(
    template_name='accounts/accept_privacy.html',
    target_field='is_accepted_privacy'))


class CommunicationsTableView(GenesisTableView):
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
            AttributeTableColumn('Reference Number', 'id'),
            AttributeTableColumn(
                'Patient',
                'patient.get_reversed_name',
                proxy_field='patient.last_name'
            ),
            AttributeTableColumn(
                'Business Partner',
                'patient.patient_profile.group.name'
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
        buttons = [
            GenesisAboveTableButton(
                'Call Log History',
                reverse('accounts:full-call-log-report')),
            GenesisAboveTableButton(
                'Resolution Report',
                reverse(
                    'accounts:configure-communications-resolution-report')),
            GenesisAboveTableButton(
                'Call Log Report',
                reverse('accounts:configure-call-log-report')),
        ]
        if self.should_show_closed():
            buttons.append(
                GenesisAboveTableButton(
                    'Hide Closed',
                    reverse('accounts:communications'))
            )
        else:
            buttons.append(
                GenesisAboveTableButton(
                    'Show Closed',
                    reverse('accounts:communications') +
                    "?show_closed=1")
            )
        return buttons

    def get_page_title(self):
        return 'Communications'

    def get_queryset(self):
        qs = PatientCommunication.objects.all()
        if self.should_show_closed():
            return qs.filter(status__is_closed=True)
        return qs.filter(status__is_closed=False)

    def should_show_closed(self):
        return bool(self.request.GET.get('show_closed', False))
communications = user_passes_test(admin_user)(
    CommunicationsTableView.as_view())


class CommunicationsResolutionConfigureView(GenesisFormView):
    form_class = PickStartEndMonthForm
    page_title = 'Configure Communications Resolution Report'
    success_message = 'Your report has been generated.'

    def get_success_url(self, form):
        dt_format = "%Y/%m/%d"
        date_info = {
            'start_date': form.cleaned_data['start_date'].strftime(dt_format),
            'end_date': form.cleaned_data['end_date'].strftime(dt_format)
        }
        return "{0}?{1}".format(
            reverse('accounts:communications-resolution-report'),
            urlencode(date_info)
        )
configure_communications_resolution_report = user_passes_test(admin_user)(
    CommunicationsResolutionConfigureView.as_view())


class CommunicationsResolutionReportView(ReportView):
    template_name = 'accounts/patients/reports/communication_resolution.html'
    filename = 'communication resolution.pdf'
    page_title = 'Communication Resolution Report'
    response_class = PDFPrintURLResponse

    def get_context_data(self):
        tz = get_default_timezone()
        start_date, end_date = self.get_timeframe()
        start_date = tz.localize(datetime.combine(start_date, time()))
        end_date = tz.localize(datetime.combine(end_date, time()))
        cur_date = tz.localize(
            datetime.combine(
                date(start_date.year, start_date.month, 1), time()))
        months = []
        while (cur_date.year < end_date.year or
                cur_date.month <= end_date.month):
            months.append((
                cur_date,
                cur_date + relativedelta(months=1) - timedelta(microseconds=1),
                cur_date.strftime('%b-%Y')
            ))
            cur_date += relativedelta(months=1)
        queryset = PatientCommunication.objects.filter(
            datetime_closed__range=(start_date, end_date),
            status__is_closed=True)
        categories = map(
            lambda x: x['resolution__name'],
            queryset.values('resolution__name').distinct()
        )
        series = []
        for month_start, month_end, month_name in months:
            month_qs = queryset.filter(
                datetime_closed__range=(month_start, month_end))
            series_data = []
            for category in categories:
                series_data.append(
                    month_qs.filter(resolution__name=category).count())
            series.append({
                'name': "{0}: {1}".format(month_name, month_qs.count()),
                'data': series_data
            })
        chart_title = 'Communication Resolution {0} - {1}'.format(
            start_date.strftime('%b %Y'), end_date.strftime('%b %Y'))
        return {
            'categories': categories,
            'series': series,
            'chart_title': chart_title,
            'new_records': PatientCommunication.objects.filter(
                datetime_added__range=(start_date, end_date)).count(),
            'open_records': PatientCommunication.objects.filter(
                status__is_closed=False).count(),
            'resolved_records': queryset.count(),
            'querystring': urlencode({
                'start_date': start_date.strftime("%Y/%m/%d"),
                'end_date': end_date.strftime("%Y/%m/%d")
            })
        }

    def get_timeframe(self):
        default_start_dt = now() - relativedelta(months=3)
        default_start_date = date(
            default_start_dt.year,
            default_start_dt.month,
            1)
        if 'start_date' in self.request.GET:
            _start_date = parse(self.request.GET['start_date'])
            start_date = date(_start_date.year, _start_date.month, 1)
        else:
            start_date = default_start_date
        if 'end_date' in self.request.GET:
            _end_date = parse(self.request.GET['end_date'])
            end_date = (
                datetime(_end_date.year, _end_date.month, 1) +
                relativedelta(months=1) - timedelta(microseconds=1)).date()
        else:
            end_date = start_date + relativedelta(months=4)
        return start_date, end_date
communications_resolution_report = user_passes_test(admin_user)(
    CommunicationsResolutionReportView.as_view())
communications_resolution_report_print = user_passes_test(admin_user)(
    CommunicationsResolutionReportView.as_view(
        template_name='accounts/patients/reports/communication_resolution_print.html'))  # noqa
communications_resolution_report_pdf = user_passes_test(admin_user)(
    CommunicationsResolutionReportView.as_view(
        template_name='accounts/patients/reports/communication_resolution_print.html',  # noqa
        output_format='pdf'))


class CallLogReportConfigureView(GenesisFormView):
    form_class = PickStartEndMonthForm
    page_title = 'Configure Call Log Report'
    success_message = 'Your report has been generated.'

    def get_success_url(self, form):
        dt_format = "%Y/%m/%d"
        date_info = {
            'start_date': form.cleaned_data['start_date'].strftime(dt_format),
            'end_date': form.cleaned_data['end_date'].strftime(dt_format)
        }
        return "{0}?{1}".format(
            reverse('accounts:call-log-report'),
            urlencode(date_info)
        )
configure_call_log_report = user_passes_test(admin_user)(
    CallLogReportConfigureView.as_view())


class CallLogReportView(ReportView):
    template_name = 'accounts/patients/reports/call_log.html'
    filename = 'call log.pdf'
    page_title = 'Call Log Report'
    response_class = PDFPrintURLResponse

    def get_context_data(self):
        start_date, end_date = self.get_timeframe()
        my_tz = get_default_timezone()
        cur_date = my_tz.localize(
            datetime(start_date.year, start_date.month, 1))
        months = []
        while (cur_date.year < end_date.year or (
                cur_date.year == end_date.year and
                cur_date.month <= end_date.month)):
            formatted_name = cur_date.strftime('%b-%Y')
            months.append((
                cur_date,
                cur_date + relativedelta(months=1) - timedelta(microseconds=1),
                formatted_name
            ))
            cur_date += relativedelta(months=1)
        charts = []
        comm_categories = CommunicationCategory.objects.all()
        # Filter categories.
        base_qs = PatientCommunication.objects.filter(
            datetime_closed__range=(start_date, end_date))
        comm_categories = filter(
            lambda x: base_qs.filter(category=x).count() > 0,
            comm_categories)
        # Iterate through comm categories and make a chart for each
        # where the "categories" for the chart are the subcategories
        for comm_category in comm_categories:
            subcats = map(
                lambda x: x['name'],
                comm_category.subcategories.values('name')
            )
            # Filter subcats down to ones that have entries
            # for this period.
            comm_qs = base_qs.filter(category=comm_category)
            subcats = filter(
                lambda x: comm_qs.filter(subcategory__name=x).count(),
                subcats
            )
            series = []
            for month_start, month_end, month_name in months:
                series_data = []
                month_qs = comm_qs.filter(datetime_closed__range=(
                    month_start, month_end))
                for subcat in subcats:
                    series_data.append(
                        month_qs.filter(subcategory__name=subcat).count())
                series.append({
                    'name': "{0}: {1}".format(month_name, sum(series_data)),
                    'data': series_data
                })
            chart_data = {
                'chart_title': comm_category,
                'series': series,
                'categories': subcats,
                'element_id': 'chart-{0}'.format(len(charts) + 1)
            }
            charts.append(chart_data)
        # Calculate by category counts
        count_data = base_qs.filter(
            category__in=comm_categories).values(
            'category__name').order_by(
            'category__name').annotate(
            category_count=Count('id'))
        by_category_count = []
        for row in count_data:
            by_category_count.append(
                (row['category__name'], row['category_count'])
            )
        # Calculate by quality improvement category
        by_qi_cat = []
        for qi_name, hr_name in PatientCommunicationNote.QI_CATEGORY_CHOICES:
            count = base_qs\
                .filter(
                    notes__quality_improvement_category=qi_name)\
                .distinct().count()
            by_qi_cat.append((hr_name, count))
        # Calculate calls by month
        by_month = []
        for month_start, month_end, month_name in months:
            count = base_qs.filter(
                datetime_closed__range=(month_start, month_end)).count()
            by_month.append((month_name, count))
        # Calculate calls by api partner, get top 5
        count_data = base_qs\
            .filter(patient__patient_profile__group__isnull=False)\
            .values('patient__patient_profile__group__name')\
            .annotate(call_count=Count('id'))\
            .order_by('-call_count')[:5]
        by_group = map(
            lambda x: (x['patient__patient_profile__group__name'],
                       x['call_count']),
            count_data
        )
        total_group_count = reduce(
            lambda x, y: x + y[1], by_group, 0)
        # Calculate calls by replacement
        count_data = base_qs\
            .filter(notes__replacements__isnull=False)\
            .values('notes__replacements__name')\
            .annotate(call_count=Count('id'))\
            .order_by('-call_count')
        by_replacement = map(
            lambda x: (x['notes__replacements__name'],
                       x['call_count']),
            count_data
        )
        total_replacement_count = reduce(
            lambda x, y: x + y[1], by_replacement, 0)
        return {
            'charts': charts,
            'start_date': start_date,
            'end_date': end_date,
            'by_group': by_group,
            'by_category_count': by_category_count,
            'by_qi_cat': by_qi_cat,
            'by_month': by_month,
            'by_replacement': by_replacement,
            'total_replacement_count': total_replacement_count,
            'total_group_count': total_group_count,
            'total_count': base_qs.count(),
            'querystring': urlencode({
                'start_date': start_date.strftime("%Y/%m/%d"),
                'end_date': end_date.strftime("%Y/%m/%d")
            })
        }

    def get_timeframe(self):
        default_start_dt = now() - relativedelta(months=3)
        my_tz = get_default_timezone()
        default_start_date = my_tz.localize(datetime(
            default_start_dt.year,
            default_start_dt.month,
            1))
        if 'start_date' in self.request.GET:
            _start_date = parse(self.request.GET['start_date'])
            start_date = my_tz.localize(
                datetime(_start_date.year, _start_date.month, 1))
        else:
            start_date = default_start_date
        if 'end_date' in self.request.GET:
            _end_date = parse(self.request.GET['end_date'])
            end_date = my_tz.localize(
                datetime(_end_date.year, _end_date.month, 1) +
                relativedelta(months=1) - timedelta(microseconds=1))
        else:
            end_date = start_date + relativedelta(months=4)
        return start_date, end_date
call_log_report = user_passes_test(admin_user)(
    CallLogReportView.as_view())
call_log_report_print = user_passes_test(admin_user)(
    CallLogReportView.as_view(
        template_name='accounts/patients/reports/call_log_print.html'))
call_log_report_pdf = user_passes_test(admin_user)(
    CallLogReportView.as_view(
        template_name='accounts/patients/reports/call_log_print.html',
        output_format='pdf'))
