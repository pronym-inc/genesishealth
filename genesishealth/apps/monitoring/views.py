from calendar import timegm
from datetime import datetime, timedelta
from json import dumps
from math import floor

from django import forms
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse
from django.http import HttpResponse
from django.utils.timezone import now
from django.views.generic import TemplateView, View

from genesishealth.apps.monitoring.models import ScalabilityTest
from genesishealth.apps.utils.class_views import (
    AttributeTableColumn, GenesisAboveTableButton, GenesisTableView
)
from genesishealth.apps.utils.forms import GenesisModelForm
from genesishealth.apps.utils.request import (
    admin_user, superuser_user, require_admin_permission)
from genesishealth.apps.utils.views import generic_form

from pytz import UTC

from .models import (
    DatabaseServer, DatabaseSnapshot,
    ReadingServer, ReadingServerSnapshot,
    WebServer, WebServerSnapshot,
    WorkerServer, WorkerSnapshot)

admin_test = user_passes_test(admin_user)


class MonitoringDashboardView(TemplateView):
    template_name = 'monitoring/dashboard.html'

    def get_context_data(self, **kwargs):
        data = super(MonitoringDashboardView, self).get_context_data(**kwargs)
        return data
dashboard = require_admin_permission('monitoring')(
    MonitoringDashboardView.as_view())


def get_nearest_ten_minute(dt):
    tz = dt.tzinfo
    return tz.localize(
        datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute / 10 * 10))


class MonitoringDataView(View):
    server_model = None
    snapshot_model = None
    output_fields = ['load', 'memory_free']

    def get(self, request, *args, **kwargs):
        output = self.get_output()
        return HttpResponse(dumps(output), content_type='application/json')

    def get_output(self):
        if 'start' in self.request.GET:
            period_start = UTC.localize(datetime.fromtimestamp(
                int(self.request.GET['start']) / 1000
            ))
            period_end = UTC.localize(datetime.fromtimestamp(
                int(self.request.GET['end']) / 1000
            ))
        else:
            period_end = now()
            period_start = now() - timedelta(days=2)
        period_start = get_nearest_ten_minute(period_start)
        period_end = get_nearest_ten_minute(period_end)

        # Figure out our range.  The step will be some number of 10 minute
        # intervals (our lowest resolution).

        # We should always show ~100 points.  Given that we have data
        # from every 10 minutes, we can calculate how big of a step to
        # take.
        step = max(int(floor(
            float((period_end - period_start).total_seconds()) / 60000
        )), 1)
        desired_events = []
        next_event = period_end
        while next_event > period_start:
            desired_events.append(next_event)
            next_event -= timedelta(minutes=10 * step)
        desired_events.reverse()
        output = {}
        for server in self.server_model.objects.all():
            output[server.name] = self.get_server_output(
                server, desired_events)
        return output

    def get_output_fields(self, server):
        return self.output_fields

    def get_server_output(self, server, desired_events):
        output_fields = self.get_output_fields(server)
        snapshots = self.snapshot_model.objects.filter(
            server=server,
            datetime_created__in=desired_events
        ).order_by('datetime_created').values(
            'datetime_created', *output_fields)
        server_output = {output_field: [] for
                         output_field in output_fields}
        for row in snapshots:
            timestamp = timegm(row['datetime_created'].timetuple()) * 1000
            for output_field in output_fields:
                val = row[output_field]
                server_output[output_field].append([timestamp, val])
        return server_output


class WebServerDataView(MonitoringDataView):
    server_model = WebServer
    snapshot_model = WebServerSnapshot
web_server_data = admin_test(WebServerDataView.as_view())


class DatabaseServerDataView(MonitoringDataView):
    server_model = DatabaseServer
    snapshot_model = DatabaseSnapshot
database_server_data = admin_test(DatabaseServerDataView.as_view())


class ReadingServerDataView(MonitoringDataView):
    server_model = ReadingServer
    snapshot_model = ReadingServerSnapshot
    output_fields = MonitoringDataView.output_fields + [
        'reading_response_time', 'readings_received']
reading_server_data = admin_test(ReadingServerDataView.as_view())


class WorkerServerDataView(MonitoringDataView):
    server_model = WorkerServer
    snapshot_model = WorkerSnapshot

    def get_output_fields(self, server):
        fields = super(WorkerServerDataView, self).get_output_fields(server)
        if server.is_queue_host:
            return fields + ['message_count']
        return fields
worker_server_data = admin_test(WorkerServerDataView.as_view())


class ScalabilityView(GenesisTableView):
    def create_columns(self):
        return [
            AttributeTableColumn(
                'Datetime Started', 'date_started', searchable=False,
                default_sort=True, default_sort_direction='desc'),
            AttributeTableColumn(
                'Reading Quantity', 'quantity', searchable=False),
            AttributeTableColumn(
                'Duration (seconds)', 'duration', searchable=False),
            AttributeTableColumn(
                'Completed', 'is_complete', searchable=False),
            AttributeTableColumn(
                '% successful', 'get_percent_successful',
                searchable=False),
            AttributeTableColumn(
                'Average Response Time', 'get_average_response',
                searchable=False),
            AttributeTableColumn(
                'Peak Response Time', 'get_max_response',
                searchable=False)
        ]

    def get_above_table_items(self):
        if self.request.user.is_superuser:
            return [
                GenesisAboveTableButton(
                    'Run Test', reverse('monitoring:scalability-new'))
            ]
        return []

    def get_page_title(self):
        return 'Scalability Tests'

    def get_queryset(self):
        return ScalabilityTest.objects.all()
scalability = admin_test(ScalabilityView.as_view())


class NewScalabilityForm(GenesisModelForm):
    duration = forms.IntegerField(max_value=300)

    class Meta:
        model = ScalabilityTest
        fields = ('quantity', 'duration')

    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester')
        super(NewScalabilityForm, self).__init__(*args, **kwargs)

    def clean(self):
        data = self.cleaned_data
        if (float(data['quantity']) / data['duration']) > 4:
            raise forms.ValidationError(
                'Invalid parameters.  Cannot send more than 4 readings per'
                ' second.')
        return data

    def save(self):
        if self.is_new:
            test = super(NewScalabilityForm, self).save(commit=False)
            test.requested_by = self.requester
            test.save()
            test.run()
            return test


@user_passes_test(superuser_user)
def scalability_new(request):
    return generic_form(
        request,
        form_class=NewScalabilityForm,
        form_kwargs={'requester': request.user},
        go_back_until=['monitoring:scalability']
    )
