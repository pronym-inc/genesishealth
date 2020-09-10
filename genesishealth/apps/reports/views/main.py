from datetime import date, datetime, time, timedelta
from itertools import groupby

from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models import Avg, Count, Max, Min, StdDev
from django.http import Http404, HttpResponse, StreamingHttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.timezone import now

from genesishealth.apps.accounts.models import PatientProfile
from genesishealth.apps.health_information.models import (
    HealthProfessionalTargets)
from genesishealth.apps.readings.models import GlucoseReading
from genesishealth.apps.reports.forms import (
    DisplayLogbookForm, SingleChartControlForm)
from genesishealth.apps.reports.misc import LogbookDay
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.class_views import (
    ActionItem, ActionTableColumn, AttributeTableColumn,
    GenesisAboveTableButton, GenesisAboveTableTemplateItem,
    GenesisTableLink, GenesisTableLinkAttrArg, GenesisTableView)
from genesishealth.apps.utils.func import convert_date_to_utc_datetime
from genesishealth.apps.utils.request import professional_user
from genesishealth.apps.utils.wkhtmltopdf import wkhtmltopdf

from wkhtmltopdf.views import PDFTemplateResponse, PDFTemplateView

from ..models import TemporaryDownload


def get_range_statistics(user, days):
    c = {'days': days}

    range_queryset = GlucoseReading.objects.select_related('patient')
    range_queryset = range_queryset.filter(
        patient__in=user.professional_profile.get_patients())
    range_queryset = range_queryset.filter(
        reading_datetime_utc__range=(now() - timedelta(days=days), now()))
    range_queryset = range_queryset.annotate(
        readings_last_period=Count('id')).annotate(
        average_value=Avg('glucose_value'))

    total_patients = user.professional_profile.get_patients().count()

    c['num_below_range'] = 0
    c['num_above_range'] = 0
    for reading in range_queryset:
        patient = reading.patient
        targets = HealthProfessionalTargets.objects.get_or_create(
            patient=patient, professional=user)
        if reading.glucose_value < targets.premeal_glucose_goal_minimum:
            c['num_below_range'] += 1
        elif reading.glucose_value > targets.postmeal_glucose_goal_maximum:
            c['num_above_range'] += 1

    c['num_in_range'] = (
        total_patients - c['num_below_range'] - c['num_above_range'])
    if total_patients == 0:
        for f in ('in', 'below', 'above'):
            key = 'percent_{0}_range'.format(f)
            c[key] = 0
    else:
        for f in ('in', 'below', 'above'):
            key = 'percent_{0}_range'.format(f)
            num_key = 'num_{0}_range'.format(f)
            c[key] = c[num_key] * 100. / total_patients

    c['total'] = total_patients
    return c


def get_compliance_statistics(user, days):
    c = {'days': days}

    base_queryset = GlucoseReading.objects.select_related()
    base_queryset = base_queryset.filter(
        patient__in=user.professional_profile.get_patients())
    base_queryset = base_queryset.filter(
        reading_datetime_utc__range=(now() - timedelta(days=days), now()))
    base_queryset = base_queryset.annotate(readings_last_period=Count('id'))

    total_patients = user.professional_profile.get_patients().count()
    c['num_in_compliance'] = 0
    for reading in base_queryset:
        patient = reading.patient
        targets = HealthProfessionalTargets.objects.get_or_create(
            patient=patient, professional=user)
        if reading.readings_last_period >= targets.compliance_goal:
            c['num_in_compliance'] += 1
    cats = ['in_compliance', 'no_readings', 'out_of_compliance']
    if total_patients == 0:
        for cat in cats:
            percent_key = 'percent_{0}'.format(cat)
            c[percent_key] = 0
    else:
        for cat in cats:
            percent_key = 'percent_{0}'.format(cat)
            num_key = 'num_{0}'.format(c)
            c[percent_key] = c[num_key] * 100. / total_patients
    c['total'] = total_patients

    return c


def get_dates():
    date_pattern = '%m/%d/%Y'
    c = {}
    for i in (1, 7, 14, 30, 60, 90):
        c[i] = (date.today() - timedelta(days=i - 1)).strftime(date_pattern)
    return c


def aggregate_readings(user, readings, days=0):
    aggregates = readings.aggregate(
        Avg('glucose_value'),
        Max('glucose_value'),
        Min('glucose_value'),
        Count('glucose_value'),
        StdDev('glucose_value'))
    aggregates['total'] = readings.count()
    aggregates['total_days'] = days

    readings.filter(
        glucose_value__gt=settings.GLUCOSE_LO_VALUE,
        glucose_value__lt=settings.GLUCOSE_HI_VALUE)

    aggregates['low_readings'] = readings.filter(
        glucose_value__lt=user.healthinformation.premeal_glucose_goal_minimum
    ).count()
    aggregates['high_readings'] = readings.filter(
        glucose_value__gt=user.healthinformation.postmeal_glucose_goal_maximum
    ).count()
    aggregates['hypo_readings'] = readings.filter(
        glucose_value__lt=user.healthinformation.safe_zone_minimum).count()
    aggregates['hyper_readings'] = readings.filter(
        glucose_value__gt=user.healthinformation.safe_zone_maximum).count()

    return aggregates


def group_readings_by_date_and_time_blocks(readings):
    grouping = {}
    for date_key, objs in groupby(
            readings,
            key=lambda reading: reading.reading_datetime.date()):
        grouping[date_key] = {
            (time(0, 0, 0), time(5, 30, 0)): [],
            (time(5, 30, 0), time(8, 0, 0)): [],
            (time(8, 0, 0), time(11, 0, 0)): [],
            (time(11, 0, 0), time(12, 30, 0)): [],
            (time(12, 30, 0), time(17, 0, 0)): [],
            (time(17, 0, 0), time(18, 30, 0)): [],
            (time(18, 30, 0), time(21, 30, 0)): [],
            (time(21, 30, 0), time(0, 0, 0)): [],
        }
        for obj in list(objs):
            obj_time = obj.reading_datetime.time()
            for (start, end), lst in grouping[date_key].items():
                if start <= obj_time < end:
                    lst.append(obj)
        grouping[date_key] = sorted(grouping[date_key].items())
    return sorted(grouping.items(), reverse=True)


@login_required
def index(request, patient_id=None):
    c = {}

    try:
        if patient_id:
            assert request.user.is_professional() or request.user.is_admin()
            if request.user.is_professional():
                try:
                    c['target'] = request.user.professional_profile\
                        .get_patients().get(id=patient_id)
                except User.DoesNotExist:
                    c['target'] = request.user.professional_profile \
                        .watch_list.get(user__id=patient_id).user
                c['breadcrumbs'] = [
                    Breadcrumb('Patients', reverse('accounts:manage-patients'))
                ]
            else:
                patient = PatientProfile.myghr_patients.get_users().get(
                    pk=patient_id)
                c['target'] = patient
                group = patient.patient_profile.get_group()
                if group is not None:
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
                        Breadcrumb('Users', reverse('accounts:manage-users'))
                    ]
                breadcrumbs.append(
                    Breadcrumb('Patient: {0}'.format(
                               patient.get_reversed_name()),
                               reverse('accounts:manage-patients-detail',
                                       args=[patient.pk]))
                )
                c['breadcrumbs'] = breadcrumbs
        else:
            assert request.user.is_patient()
    except (User.DoesNotExist, AssertionError):
        return HttpResponse(status=500)

    return render(request, "reports/index.html", c)


@login_required
def professional_index(request):
    assert request.user.is_professional()
    return render(request, "reports/professional_index.html")


@login_required
def logbook_with_summary(request, patient_id=None):
    try:
        if patient_id:
            assert request.user.is_professional() or request.user.is_admin()
            if request.user.is_professional():
                try:
                    user = request.user.professional_profile.get_patients().get(
                        pk=patient_id)
                except User.DoesNotExist:
                    try:
                        user = request.user.professional_profile.watch_list.get(user__pk=patient_id).user
                    except PatientProfile.DoesNotExist:
                        return HttpResponse(status=500)
            else:
                user = PatientProfile.myghr_patients.get_users().get(
                    pk=patient_id)
        else:
            assert request.user.is_patient()
            user = request.user
    except (AssertionError, User.DoesNotExist):
        return HttpResponse(status=500)

    end_datetime = datetime.now(user.patient_profile.timezone)
    start_datetime = end_datetime - timedelta(days=29)

    readings = GlucoseReading.objects.filter(
        patient=user,
        reading_datetime_utc__range=[
            start_datetime,
            end_datetime + timedelta(days=1)
        ]
    ).order_by("-reading_datetime_utc")
    grouped_readings = group_readings_by_date_and_time_blocks(readings)
    aggregates = aggregate_readings(user, readings, days=len(grouped_readings))
    c = {
        "aggregates": aggregates,
        'empty': (len(readings) == 0),
        'patient': user,
        'dates': get_dates(),
        'start_date': start_datetime.date,
        'end_date': end_datetime.date
    }
    c['forms'] = {}
    c['forms']['print'] = DisplayLogbookForm(
        patient=user, requester=request.user, prefix="print",
        initial={
            'start_date': start_datetime.date,
            'end_date': end_datetime.date
        }
    )
    if request.user.is_admin():
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
                Breadcrumb('Users', reverse('accounts:manage-users'))
            ]
        breadcrumbs.extend([
            Breadcrumb('Patient: {0}'.format(
                       user.get_reversed_name()),
                       reverse('accounts:manage-patients-detail',
                               args=[user.pk])),
            Breadcrumb('Reports',
                       reverse('reports:patient-index', args=[user.pk]))
        ])
        c['breadcrumbs'] = breadcrumbs

    return render(request, "reports/logbook/main.html", c)


def print_logbook_context(data):
    """Helper function to create context for logbook report view"""
    patient = data.get('patient')

    period_type = LogbookDay.DISPLAY_TYPES_TO_PERIOD_TYPES[
        data.get('display_type')]
    days = LogbookDay.generate_logbook_days(
        cap_entries=settings.MAX_PRINT_LOGBOOK_ENTRIES, **data)

    timezone = patient.patient_profile.timezone
    start_datetime = convert_date_to_utc_datetime(
        data.get('start_date'), timezone)
    end_datetime = convert_date_to_utc_datetime(data.get('end_date'), timezone)

    number_of_days = int(
        (end_datetime - start_datetime).total_seconds() / 60 / 60 / 24)

    previous_end_datetime = start_datetime - timedelta(days=1)
    previous_start_datetime = previous_end_datetime - timedelta(
        days=number_of_days)  # Equal periods of time

    # Calculate some stats for "this" period and previous period.
    target_range_stats = {}
    items = (
        (start_datetime, end_datetime, 'this_period'),
        (previous_start_datetime, previous_end_datetime, 'previous_period')
    )
    for i in items:
        readings = patient.glucose_readings.filter(
            reading_datetime_utc__range=(i[0], i[1]))
        aggregates = readings.aggregate(Avg('glucose_value'))
        compliance_goal = patient.healthinformation.compliance_goal
        if compliance_goal != 0:
            compliance_percent = (
                float(readings.count()) /
                number_of_days /
                compliance_goal *
                100)
        else:
            compliance_percent = 0
        hypo_readings = readings.filter(
            glucose_value__lt=patient.healthinformation.safe_zone_minimum)
        hyper_readings = readings.filter(
            glucose_value__gt=patient.healthinformation.safe_zone_maximum)

        target_range_stats[i[2]] = {
            'glucose_average': aggregates['glucose_value__avg'],
            'compliance_percent': compliance_percent,
            'hypo_count': hypo_readings.count(),
            'hyper_count': hyper_readings.count()
        }

    # Calculate aggregate statistics
    readings = patient.glucose_readings.filter(
        reading_datetime_utc__range=(start_datetime, end_datetime))
    aggregates = readings.aggregate(StdDev('glucose_value'))
    readings_in_range = readings.filter(
        glucose_value__gte=patient.healthinformation.
        premeal_glucose_goal_minimum,
        glucose_value__lte=patient.healthinformation.
        postmeal_glucose_goal_maximum)
    if readings:
        percent_in_range = float(readings_in_range.count()) / readings.count()
    else:
        percent_in_range = 0
    if number_of_days:
        average_readings_per_day = float(readings.count()) / number_of_days
    else:
        average_readings_per_day = 0
    # get AIC if we have a glucose average
    if target_range_stats['this_period']['glucose_average'] is not None:
        estimated_a1c = float(
            target_range_stats['this_period']['glucose_average'] + 77.3) / 35.6
    else:
        estimated_a1c = None

    # We can steal some of this info from target_range_stats['this_period']
    aggregate_statistics = {
        'glucose_average': target_range_stats[
            'this_period']['glucose_average'],
        'average_readings_per_day': average_readings_per_day,
        'standard_deviation': aggregates['glucose_value__stddev'],
        'percent_in_range': percent_in_range,
        'hypo_count': target_range_stats['this_period']['hypo_count'],
        'hyper_count': target_range_stats['this_period']['hyper_count'],
        'number_of_readings': readings.count(),
        'estimated_a1c': estimated_a1c
    }

    c = {'days': days,
         'patient': patient,
         'periods': LogbookDay.get_period_info(
             period_type, patient.patient_profile.timezone),
         'calculated_stats': LogbookDay.calculate_stats(days, patient),
         'start_date': start_datetime.date,
         'end_date': end_datetime.date,
         'previous_start_date': previous_start_datetime.date,
         'previous_end_date': previous_end_datetime.date,
         'current_date': now(),
         'target_info': target_range_stats,
         'number_of_days': number_of_days,
         'aggregate_statistics': aggregate_statistics
         }

    return c


class PDFPrintURLResponse(PDFTemplateResponse):
    """
    A PDF response class that points wkhtmltopdf to the external
    print url. This avoids cross domain issues for ajax.
    """

    def _get_filename(self):
        path = self._request.get_full_path().replace('pdf', 'print')
        return '{0}://{1}{2}'.format(
            settings.HTTP_PROTOCOL, settings.SITE_URL, path)

    def _get_cmd_options(self):
        cmd_options = self.cmd_options.copy()
        cmd_options['cookie'] = [
            'sessionid', self._request.COOKIES['sessionid']]
        return cmd_options

    @property
    def rendered_content(self):
        return wkhtmltopdf(
            pages=[self._get_filename()], **self._get_cmd_options())


class ReportView(PDFTemplateView):

    output_format = 'html'
    filename = 'Report.pdf'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ReportView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if self.output_format == 'html':
            self.response_class = self.html_response_class
        return super(ReportView, self).get(request, *args, **kwargs)


class LogbookReport(ReportView):
    template_name = 'reports/logbook/print/logbook.html'
    filename = 'Logbook report.pdf'
    response_class = PDFPrintURLResponse

    def get(self, request):
        try:
            form = DisplayLogbookForm(request.GET, prefix="print")
            assert form.is_valid(), repr(form.errors)
            self.data = form.cleaned_data
            patient = self.data.get('patient')
            if request.user.is_patient():
                assert request.user == patient
            elif request.user.is_professional():
                assert (
                    patient in request.user.professional_profile.get_patients()
                )
        except AssertionError as e:
            return HttpResponse(e, status=500)

        return super(LogbookReport, self).get(request)

    def get_context_data(self):
        return print_logbook_context(self.data)


class AggregateReport(ReportView):
    template_name = "reports/test_history.html"
    response_class = PDFPrintURLResponse

    def get_user(self, request, patient_id=None):
        if patient_id:
            assert request.user.is_professional() or request.user.is_admin()
            if request.user.is_professional():
                try:
                    user = request.user.professional_profile.get_patients().get(
                        pk=patient_id)
                except User.DoesNotExist:
                    try:
                        user = request.user.professional_profile.watch_list.get(user__pk=patient_id).user
                    except PatientProfile.DoesNotExist:
                        return HttpResponse(status=500)
            else:
                user = PatientProfile.myghr_patients.get_users().get(
                    pk=patient_id)
        else:
            assert request.user.is_patient()
            user = request.user
        return user

    def get(self, request, patient_id=None):
        try:
            self.user = self.get_user(request, patient_id)
        except (AssertionError, User.DoesNotExist):
            return HttpResponse(status=500)
        timezone = self.user.patient_profile.timezone
        self.dates = get_dates()
        date_data = {}

        date_format = '%m/%d/%Y'
        if request.GET.get('start_date') and request.GET.get('end_date'):
            start_date = timezone.localize(
                datetime.strptime(request.GET['start_date'], date_format))
            end_date = timezone.localize(
                datetime.strptime(request.GET['end_date'], date_format))
            days = 'custom'
        else:
            days = int(request.GET.get('days', 7))
            end_date = datetime.now(timezone)
            start_date = end_date - timedelta(days=days - 1)

        date_data = {
            'days': days,
            'start_date': start_date.strftime(date_format),
            'end_date': end_date.strftime(date_format)
        }

        self.form = SingleChartControlForm(date_data)
        if not self.form.is_valid():
            return HttpResponse(repr(self.form.errors))

        return super(AggregateReport, self).get(request)

    def post(self, request, patient_id=None):
        try:
            self.user = self.get_user(request, patient_id)
        except (AssertionError, User.DoesNotExist):
            return HttpResponse(status=500)

        self.dates = get_dates()
        self.form = SingleChartControlForm(request.POST)
        if not self.form.is_valid():
            return HttpResponse(repr(self.form.errors))
        return super(AggregateReport, self).get(request)

    def get_context_data(self):
        timezone = self.user.patient_profile.timezone
        c = {
            'patient': self.user,
            'dates': self.dates,
            'form': self.form,
            'current_date': datetime.now(timezone).date(),
        }
        data = self.form.cleaned_data
        start_datetime = timezone.localize(
            datetime.combine(data.get('start_date'), time()))
        end_datetime = timezone.localize(
            datetime.combine(data.get('end_date'), time()))
        # Add one to account for the final day.  E.g., Tuesday-Wednesday is 2
        # days, even though the difference in date is only 1.
        days = (end_datetime.date() - start_datetime.date()).days + 1

        for i in ('premeal', 'postmeal', 'combined', 'summary'):
            # Have to add one to the end_date, or it will not get readings
            # from that date
            readings = GlucoseReading.objects.filter(
                patient=self.user,
                reading_datetime_utc__range=[
                    start_datetime, end_datetime + timedelta(days=1)])
            readings = readings.exclude(measure_type="TEST mode")
            if i == 'premeal':
                c['premeal_empty'] = readings.filter(
                    measure_type=GlucoseReading.MEASURE_TYPE_BEFORE
                ).count() == 0
            elif i == 'postmeal':
                c['postmeal_empty'] = readings.filter(
                    measure_type=GlucoseReading.MEASURE_TYPE_AFTER
                ).count() == 0
            else:
                c['%s_empty' % i] = readings.count() == 0
                if i == 'summary':
                    c['aggregates'] = aggregate_readings(
                        self.user, readings, days=days)

        c['days'] = self.form.cleaned_data.get('days')
        c['start_date'] = self.form.cleaned_data.get('start_date')
        c['end_date'] = self.form.cleaned_data.get('end_date')
        if self.request.user.is_admin():
            group = self.user.patient_profile.get_group()
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
                    Breadcrumb('Users', reverse('accounts:manage-users'))
                ]
            breadcrumbs.extend([
                Breadcrumb('Patient: {0}'.format(
                           self.user.get_reversed_name()),
                           reverse('accounts:manage-patients-detail',
                                   args=[self.user.pk])),
                Breadcrumb('Reports',
                           reverse('reports:patient-index',
                                   args=[self.user.pk]))
            ])
            c['breadcrumbs'] = breadcrumbs
        return c


@login_required
def summary_report(request, patient_id=None):
    try:
        if patient_id:
            if request.user.is_professional():
                patient = request.user.professional_profile.get_patients().get(
                    pk=patient_id)
            elif request.user.is_admin():
                patient = PatientProfile.myghr_patients.get_users().get(
                    pk=patient_id)
            else:
                raise AssertionError
        else:
            assert request.user.is_patient()
            patient = request.user
    except (User.DoesNotExist, AssertionError):
        return HttpResponse(status=500)
    end = now()
    start = now() - timedelta(days=14)
    c = {
        'patient': patient,
        'start_date': start,
        'end_date': end,
        'forms': {'print': DisplayLogbookForm(
            patient=patient,
            requester=request.user,
            prefix="print")}
    }
    if request.user.is_admin():
        group = patient.patient_profile.get_group()
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
                Breadcrumb('Users', reverse('accounts:manage-users'))
            ]
        breadcrumbs.extend([
            Breadcrumb('Patient: {0}'.format(
                       patient.get_reversed_name()),
                       reverse('accounts:manage-patients-detail',
                               args=[patient.pk])),
            Breadcrumb('Reports',
                       reverse('reports:patient-index', args=[patient.pk]))
        ])
        c['breadcrumbs'] = breadcrumbs
    return render(request, 'reports/summary_report.html', c)


class BaseReportTableView(GenesisTableView):
    def get_days(self):
        days = int(self.request.GET.get('days', 7))
        assert days in (1, 7, 14, 30, 60, 90)
        return days

    def get_display_filter(self):
        view = self.request.GET.get("view", self.allowed_views[0])
        assert view in self.allowed_views
        return view


class ComplianceTableView(BaseReportTableView):
    additional_js_templates = ['reports/compliance_js.html', ]
    allowed_views = ('non-compliant', 'compliant', 'no-readings')

    def create_columns(self):
        days = self.get_days()
        return [
            AttributeTableColumn('Last Name', 'last_name', cell_class='main'),
            AttributeTableColumn('First Name', 'first_name'),
            AttributeTableColumn(
                'Contact #',
                'patient_profile.contact.phone',
                sortable=False),
            AttributeTableColumn(
                'Compliance',
                'patient_profile.stats.readings_last_{0}'.format(days),
                string_format='%1.f'),
            AttributeTableColumn(
                'Testing Compliance',
                'patient_profile.get_compliance_for_professional',
                func_args=[self.request.user],
                searchable=False),
            AttributeTableColumn(
                'Last Reading Date',
                'patient_profile.get_last_reading_display',
                searchable=False),
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
        display_filter = self.get_display_filter()
        items = []
        if display_filter == 'compliant':
            items.append(
                GenesisAboveTableButton(
                    'Show Non-Compliant',
                    button_id='show-non-compliant'
                )
            )
        else:
            items.append(
                GenesisAboveTableButton(
                    'Show Compliant',
                    button_id='show-compliant'
                )
            )
        items.append(
            GenesisAboveTableTemplateItem('reports/datepicker_include.html')
        )
        return items

    def get_page_title(self):
        return {
            'compliant': 'Compliant Patients',
            'no-readings': 'Patients With No Readings',
            'non-compliant': 'Non-Compliant Patients'
        }[self.get_display_filter()]

    def get_queryset(self):
        days = self.get_days()
        view = self.get_display_filter()
        prof = self.request.user.professional_profile
        if view == 'compliant':
            qs = prof.get_in_compliance_patients(days)
        elif view == 'no-readings':
            qs = prof.get_patients_with_no_readings(days)
        else:
            qs = prof.get_out_of_compliance_patients(days)
        return qs


prof_test = user_passes_test(professional_user)
compliance = prof_test(ComplianceTableView.as_view())


@user_passes_test(professional_user)
def compliance_landing(request):
    c = {'compliance': get_compliance_statistics(
        request.user,
        request.POST.get('compliance_days') and
        int(request.POST.get('compliance_days')) or 1),
    }

    return render(request, 'reports/compliance_landing.html', c)


@user_passes_test(professional_user)
def compliance_report(request, user_id):
    """Compliance report for an individual user.  Not currently used."""
    try:
        user = request.user.professional_profile.get_patients().get(pk=user_id)
    except User.DoesNotExist:
        try:
            user = request.user.professional_profile.watch_list.get(user__pk=user_id).user
        except PatientProfile.DoesNotExist:
            return HttpResponse(status=500)

    c = {'user': user}
    return render(request, 'reports/compliance_report.html', c)


class RangeReportTableView(BaseReportTableView):
    additional_js_templates = ('reports/range_js.html',)
    allowed_views = ('all', 'below-range', 'above-range', 'in-range')

    def create_columns(self):
        days = self.get_days()
        return [
            AttributeTableColumn('Last Name', 'last_name', cell_class='main'),
            AttributeTableColumn('First Name', 'first_name'),
            AttributeTableColumn(
                'Contact #',
                'patient_profile.contact.phone',
                sortable=False),
            AttributeTableColumn(
                'Daily Glucose',
                'patient_profile.stats.average_value_last_{0}'.format(days),
                string_format='%1.f', searchable=False),
            AttributeTableColumn(
                'Target Ranges',
                'patient_profile.target_range_breakdown',
                func_args=[self.request.user],
                searchable=False),
            AttributeTableColumn(
                'Last Reading Date',
                'patient_profile.get_last_reading_display',
                searchable=False),
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
            GenesisAboveTableTemplateItem('reports/datepicker_include.html')
        ]

    def get_page_title(self):
        return 'My Target Range Report'

    def get_queryset(self):
        view = self.get_display_filter()
        days = self.get_days()
        prof = self.request.user.professional_profile
        if view == 'below-range':
            queryset = prof.get_patients_by_range(days, 'below')
        elif view == 'above-range':
            queryset = prof.get_patients_by_range(days, 'above')
        elif view == 'in-range':
            queryset = prof.get_patients_by_range(days, 'inside')
        else:
            queryset = prof.get_patients()
        return queryset

range_report = prof_test(RangeReportTableView.as_view())


@user_passes_test(professional_user)
def range_landing(request):
    c = {}
    c['range'] = get_range_statistics(
        request.user,
        request.POST.get('range_days') and
        int(request.POST.get('range_days')) or 1)

    return render(request, 'reports/range_landing.html', c)


class TempDownloadTableView(GenesisTableView):
    page_title = "My Downloads"

    def create_columns(self):
        return [
            AttributeTableColumn(
                'Download Date/Time',
                'datetime_added',
                default_sort=True,
                default_sort_direction="desc"),
            AttributeTableColumn('Valid Until', 'valid_until'),
            AttributeTableColumn('Filename', 'filename'),
            ActionTableColumn(
                'Download',
                actions=[
                    ActionItem(
                        'Download',
                        GenesisTableLink(
                            'reports:temp-download',
                            url_args=[GenesisTableLinkAttrArg('pk')],
                            prefix="")
                    )
                ])
        ]

    def get_queryset(self):
        return self.request.user.temporary_downloads.filter(
            valid_until__gt=now())


temp_download_index = TempDownloadTableView.as_view()


def temp_download(request, download_id):
    try:
        dl = TemporaryDownload.objects.exclude(
            valid_until__isnull=False, valid_until__lt=now()).get(
            for_user=request.user, pk=download_id)
    except TemporaryDownload.DoesNotExist:
        raise Http404
    response = StreamingHttpResponse(dl.content, content_type=dl.content_type)
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(
        dl.filename)
    return response
