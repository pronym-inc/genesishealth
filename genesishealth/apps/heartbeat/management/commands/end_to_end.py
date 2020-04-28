import sys
import time

from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.timezone import now

from genesishealth.apps.api.models import APILogRecord
from genesishealth.apps.gdrives.models import GDrive
from genesishealth.apps.readings.models import GlucoseReading

import paramiko


def send_restart_command(reading_server):
    key = paramiko.RSAKey.from_private_key_file(
        settings.REMOTE_ACCESS_SSH_KEY_PATH)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    port = settings.REMOTE_ACCESS_SSH_PORT_MAP[reading_server]
    client.connect(hostname=reading_server,
                   port=port,
                   pkey=key,
                   username=settings.REMOTE_ACCESS_SSH_USERNAME)
    client.exec_command(settings.AUTORESTART_COMMAND)


class EndToEndException(Exception):
    def __init__(self, message, is_connection_error=False):
        super(EndToEndException, self).__init__(message)
        self.is_connection_error = is_connection_error


def do_test(device, reading_server):
    user = device.patient
    start_time = now()
    # Send reading
    try:
        response, reading_data = user.patient_profile.send_http_reading(
            reading_server=reading_server)
        assert response
    except:
        raise EndToEndException(
            '[{0}] Error connecting to reading server'.format(
                reading_server), is_connection_error=True)
    # Verify it's there and wait a few seconds before re-checking.
    for i in range(10):
        try:
            reading = user.glucose_readings.get(
                reading_datetime_utc__gt=start_time - timedelta(seconds=10),
                glucose_value=reading_data['value_1']
            )
        except GlucoseReading.DoesNotExist:
            time.sleep(.5)
        else:
            break
    else:
        raise EndToEndException(
            '[{0}] Reading not found in database.'.format(
                reading_server))
    if settings.END_TO_END_SKIP_API:
        return
    # Assume reading is latest one by db ID.
    reading = user.glucose_readings.order_by('-id')[0]
    # See if API record was sent.
    for i in range(10):
        qs = APILogRecord.objects.filter(
            is_inbound=False, data__contains=reading.glucose_value,
            datetime__gt=start_time)
        if qs.count() > 0:
            break
        time.sleep(.5)
    else:
        raise EndToEndException(
            '[{0}] Reading not received by API.'.format(
                reading_server))


class Command(BaseCommand):
    def handle(self, **options):
        # Test all the reading servers.
        try:
            device = GDrive.objects.filter(
                is_verizon_testing_device=True,
                patient__isnull=False).order_by('?')[0]
        except IndexError:
            print('No test devices configured.')
            sys.exit(2)
        warnings = []
        for reading_server in settings.READING_SERVER_LOCATIONS:
            try:
                do_test(device, reading_server)
            except EndToEndException as e:
                succeeded = False
                exit_message = ""
                if e.is_connection_error:
                    # Try restarting the server.
                    send_restart_command(reading_server)
                    time.sleep(5)
                    try:
                        do_test(device, reading_server)
                    except EndToEndException as e2:
                        exit_message = str(e2)
                    else:
                        succeeded = True
                        warnings.append(
                            "Restarted {0}.".format(reading_server))
                else:
                    exit_message = str(e)
                if not succeeded:
                    print(exit_message)
                    sys.exit(2)
        if len(warnings) > 0:
            exit_message = ", ".join(warnings)
            print(exit_message)
            sys.exit(1)
