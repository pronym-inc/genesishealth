import re

from django.conf import settings
from django.utils.timezone import now

from genesishealth.apps.gdrives.models import GDrive

import paramiko


def make_client(location):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if settings.REMOTE_ACCESS_SSH_KEY_PASSWORD:
        passwd = settings.REMOTE_ACCESS_SSH_KEY_PASSWORD
    else:
        passwd = None
    key = paramiko.RSAKey.from_private_key_file(
        settings.REMOTE_ACCESS_SSH_KEY_PATH, password=passwd)
    port = settings.REMOTE_ACCESS_SSH_PORT_MAP.get(location)
    client.connect(
        hostname=location,
        port=port,
        pkey=key,
        username=settings.REMOTE_ACCESS_SSH_USERNAME)
    return client


def get_free_memory(location=None, client=None):
    if client is None:
        client = make_client(location)
    _, stdout, _ = client.exec_command('free -m')
    out = stdout.read()
    free_mem = int(re.findall('Mem:\s+\d+\s+\d+\s+(\d+)\s+', out)[0])
    return free_mem


def get_load(location=None, client=None):
    if client is None:
        client = make_client(location)
    _, stdout, _ = client.exec_command('uptime')
    out = stdout.read()
    loads = map(
        lambda x: float(x.replace(',', '')),
        re.findall('\d+\.\d{2}(?:,|$)', out)
    )
    return loads


def get_message_count(location):
    client = make_client(location)
    _, stdout, _ = client.exec_command(
        'sudo rabbitmqctl list_queues -p /genesishealth')
    out = stdout.read()
    return int(re.findall('celery\t(\d+)', out)[0])


def get_reading_response_time(location):
    try:
        device = GDrive.objects.filter(
            is_verizon_testing_device=True,
            patient__isnull=False).order_by('?')[0]
    except IndexError:
        raise Exception('No test devices configured.')
    user = device.patient
    start = now()
    user.patient_profile.send_http_reading(reading_server=location)
    return (now() - start).total_seconds()
