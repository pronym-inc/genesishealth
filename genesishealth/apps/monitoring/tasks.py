import socket

from datetime import datetime
from random import choice

from celery import group
from celery.schedules import crontab
from celery.task import periodic_task, task

from django.db import IntegrityError
from django.utils.timezone import now

from pytz import UTC


@periodic_task(run_every=crontab(minute="*/10"))
def update_monitoring():
    from .models import (
        DatabaseServer, ReadingServer, WebServer, WorkerServer)
    rn = now()
    # Odd as they look, these arithmetic gymanistics round down to the nearest
    # 10 minute mark which will standardize the timestamp.
    dt = UTC.localize(
        datetime(rn.year, rn.month, rn.day, rn.hour, rn.minute / 10 * 10))
    for typ in (DatabaseServer, ReadingServer, WebServer, WorkerServer):
        # noinspection PyUnresolvedReferences
        for s in typ.objects.all():
            s.make_snapshot(dt)


class ReadingResult(object):
    def __init__(self, is_success, response_time, reading_server_id):
        self.is_success = is_success
        self.response_time = response_time
        self.reading_server_id = reading_server_id


@task
def scalability_test(test_id):
    from .models import ScalabilityTest, ReadingServer
    from genesishealth.apps.accounts.models import PatientProfile
    from genesishealth.apps.gdrives.models import GDrive
    meid_suffix = 0
    test_device_ids = []
    test = ScalabilityTest.objects.get(id=test_id)
    quantity = test.quantity
    duration = test.duration
    for i in range(20):
        while True:
            meid = 'SCALATESTDEV{0}'.format(meid_suffix)
            try:
                new_drive = GDrive.objects.create(
                    meid=meid,
                    device_id="ID" + meid,
                    is_scalability_device=True)
            except IntegrityError:
                meid_suffix += 1
            else:
                meid_suffix += 1
                break
        test_device_ids.append(new_drive.id)
        patient = PatientProfile.myghr_patients.create_user(
            'SCALA', 'TEST')
        new_drive.register(patient)
    reading_server_ids = map(
        lambda x: x['id'],
        ReadingServer.objects.all().values('id')
    )
    step = float(duration) / quantity
    grp = group(send_test_reading.subtask(
        (choice(test_device_ids), choice(reading_server_ids)),
        countdown=step * i)
        for i in range(quantity))
    (grp | finish_scalability_test.s(
        quantity, duration, test_device_ids, test.id))()


class ScalabilityTestResult(object):
    def __init__(self, quantity, duration):
        self.quantity = quantity
        self.duration = duration
        self.results = {}

    def add_result(self, result):
        if result.reading_server_id not in self.results:
            self.results[result.reading_server_id] = {
                'success_count': 0,
                'fail_count': 0,
                'response_times': []
            }
        if result.is_success:
            self.results[result.reading_server_id]['success_count'] += 1
        else:
            self.results[result.reading_server_id]['fail_count'] += 1
        self.results[result.reading_server_id]['response_times'].append(
            result.response_time)

    def get_average_response_times(self):
        output = {}
        for server_id, data in self.results.items():
            output[server_id] = float(
                sum(data['response_times'])) / len(data['response_times'])
        return output


@task
def send_test_reading(device_id, reading_server_id):
    from .models import ReadingServer
    print('Sending test reading.')
    from genesishealth.apps.gdrives.models import GDrive
    gdrive = GDrive.objects.get(pk=device_id)
    reading_server = ReadingServer.objects.get(pk=reading_server_id)
    start = now()
    try:
        success, _ = gdrive.patient.patient_profile.send_http_reading(
            reading_server=reading_server.location)
    except socket.timeout:
        success = False
    total_time = (now() - start).total_seconds()
    return ReadingResult(success, total_time, reading_server_id)


@task
def finish_scalability_test(
        reading_results, quantity, duration, test_device_ids, test_id):
    from .models import (
        ReadingServer, ScalabilityTest, ScalabilityResult)
    from genesishealth.apps.gdrives.models import GDrive
    test = ScalabilityTest.objects.get(id=test_id)
    for result in reading_results:
        reading_server = ReadingServer.objects.get(pk=result.reading_server_id)
        ScalabilityResult.objects.create(
            test=test,
            reading_server=reading_server,
            response_time=result.response_time,
            is_success=result.is_success)
    for device_id in test_device_ids:
        device = GDrive.objects.get(pk=device_id)
        device.readings.all().delete()
        device.patient.delete()
        device.delete()
    test.is_complete = True
    test.save()
