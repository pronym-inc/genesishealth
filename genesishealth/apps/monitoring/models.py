from datetime import timedelta

from django.db import models
from django.db.models import Avg, Max
from django.utils.timezone import now

from .func import (
    get_free_memory, get_load, get_message_count, get_reading_response_time,
    make_client)


class ServerSnapshot(models.Model):
    class Meta:
        abstract = True

    datetime_created = models.DateTimeField()
    load = models.FloatField()
    memory_free = models.PositiveIntegerField()

    @classmethod
    def create_snapshot(
            cls, server, client=None, dt=None):
        client = make_client(server.location)
        return cls.objects.create(
            **cls.get_snapshot_kwargs(server, client, dt))

    @classmethod
    def get_snapshot_kwargs(cls, server, client, dt):
        load = get_load(client=client)[1]
        memory_free = get_free_memory(client=client)
        if dt is None:
            dt = now()
        return {
            'datetime_created': dt,
            'server': server,
            'load': load,
            'memory_free': memory_free
        }


class DatabaseSnapshot(ServerSnapshot):
    server = models.ForeignKey(
        'DatabaseServer', related_name='snapshots', on_delete=models.CASCADE)


class WorkerSnapshot(ServerSnapshot):
    server = models.ForeignKey(
        'WorkerServer', related_name='snapshots', on_delete=models.CASCADE)
    message_count = models.PositiveIntegerField(null=True)

    @classmethod
    def get_snapshot_kwargs(cls, server, client, dt):
        kwargs = super(WorkerSnapshot, cls).get_snapshot_kwargs(
            server, client, dt)
        if server.is_queue_host:
            kwargs['message_count'] = get_message_count(server.location)
        return kwargs


class ReadingServerSnapshot(ServerSnapshot):
    server = models.ForeignKey(
        'ReadingServer', related_name='snapshots', on_delete=models.CASCADE)
    reading_response_time = models.FloatField()
    readings_received = models.PositiveIntegerField()

    @classmethod
    def get_snapshot_kwargs(cls, server, client, dt):
        kwargs = super(ReadingServerSnapshot, cls).get_snapshot_kwargs(
            server, client, dt)
        kwargs['reading_response_time'] = get_reading_response_time(
            server.location)
        range_start = dt - timedelta(minutes=10)
        range_end = dt
        kwargs['readings_received'] = server.log_entries.filter(
            date_created__range=(range_start, range_end)
        ).count()
        return kwargs


class WebServerSnapshot(ServerSnapshot):
    server = models.ForeignKey(
        'WebServer', related_name='snapshots', on_delete=models.CASCADE)


class BaseServer(models.Model):
    class Meta:
        abstract = True

    name = models.CharField(max_length=255, unique=True)
    location = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    def make_snapshot(self, dt):
        self.snapshot_class.create_snapshot(self, dt=dt)


class DatabaseServer(BaseServer):
    snapshot_class = DatabaseSnapshot


class WebServer(BaseServer):
    snapshot_class = WebServerSnapshot


class WorkerServer(BaseServer):
    snapshot_class = WorkerSnapshot

    is_queue_host = models.BooleanField(default=False)


class ReadingServer(BaseServer):
    snapshot_class = ReadingServerSnapshot

    log_alias = models.CharField(max_length=255, unique=True)


class ScalabilityTest(models.Model):
    quantity = models.PositiveIntegerField()
    duration = models.PositiveIntegerField()
    date_started = models.DateTimeField(auto_now_add=True)
    is_complete = models.BooleanField(default=False)
    requested_by = models.ForeignKey('auth.User', null=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ('-date_started',)

    def get_average_response(self):
        agg = self.results.aggregate(avg_response=Avg('response_time'))
        return agg['avg_response']

    def get_max_response(self):
        agg = self.results.aggregate(max_response=Max('response_time'))
        return agg['max_response']

    def get_percent_successful(self):
        return 100 * float(
            self.results.filter(is_success=True).count()) / self.quantity

    def run(self):
        from genesishealth.apps.monitoring.tasks import scalability_test
        scalability_test.delay(self.id)


class ScalabilityResult(models.Model):
    test = models.ForeignKey(ScalabilityTest, related_name='results', on_delete=models.CASCADE)
    reading_server = models.ForeignKey(
        ReadingServer, related_name='scalability_results', on_delete=models.CASCADE)
    response_time = models.FloatField()
    is_success = models.BooleanField()
