import sys
from multiprocessing import Pool
import time
from importlib import import_module
import random
import socket

from django.core.management.base import BaseCommand
from django.utils.timezone import now

from genesishealth.apps.readings.models import GlucoseReading


time_limit = 5  # If a process hangs more than 5 seconds before returning something, game over.


def err(msg):
    sys.stderr.write(str(msg))


def debug_msg(msg, debug):
    if debug:
        print(msg)


def new_process_remote(host, port, meid, serial_num, debug, wait_for_output=True, timeout=None):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if timeout:
        sock.settimeout(timeout)
    sock.connect((host, port))
    reading = generate_random_reading(meid, serial_num)
    debug_msg('Sending %s to %s' % (reading, host), debug)
    start_time = now()
    sock.send(reading)
    if wait_for_output:
        output = sock.recv(4096)
        debug_msg('%s - %s' % (host, output), debug)
    total_time = now() - start_time
    return {'success': True, 'total_time': total_time.total_seconds()}


def generate_random_reading(meid, serial_num):
    c = {
        'gateway_type': '4123',
        'gateway_id': '0000000000000001',
        'device_type': '4123',
        'serial_number': serial_num,
        'meid': meid,
        'extension_id': '1',
        'year': '2013',
        'month': random.randint(1, 12),
        'day': random.randint(1, 28),
        'hour': '%01d,-05' % random.randint(0, 23),
        'minute': random.randint(0, 59),
        'second': random.randint(0, 59),
        'data_type': '1',
        'value_1': random.randint(80, 190),
        'value_2': '0',
        'value_3': '0',
        'value_4': '1',
        'value_5': '0',
        'value_6': '0'
    }
    return GlucoseReading.raw_reading_from_dict(c)


class Command(BaseCommand):
    args = "<number of readings to send> <number to send at once> <name of settings file to use (optional)"
    help = "Generates a (potentially) large quantity of readings and then records how long it takes the server\
        to process them."
    
    def handle(self, max_processes=10, total_tests=500, environment_settings=None, debug=False, *args, **options):
        if environment_settings:
            target_settings = import_module('genesishealth.conf.%s.settings' % environment_settings)
        else:
            from django.conf import settings as target_settings

        # Create a worker pool and get it going.
        max_processes = int(max_processes)
        total_tests = int(total_tests)
        pool = Pool(processes=max_processes)
        results = []
        start_time = now()
        for i in range(total_tests):
            meid, serial = random.choice(target_settings.SCALABILITY_DEVICES)
            results.append(pool.apply_async(new_process_remote, (
                random.choice(target_settings.READING_SERVER_LOCATIONS),
                target_settings.GDRIVE_READING_PORT,
                meid,
                serial,
                debug
            )))

        data = []
        while True:
            new_results = []
            for result in results:
                if result.ready():
                    try:
                        r = result.get(timeout=5)
                    except socket.error:
                        pass
                    else:
                        data.append(r)
                        continue
                new_results.append(result)
            if len(new_results) == 0:
                break
            results = new_results
            time.sleep(1)
        # Print total time.
        total_time = now() - start_time
        print(
            'Total time to execute %s processes: %s' % (total_tests, total_time.total_seconds())
        )
        successes = [d for d in data if d['success']]
        print('Number of successes: %s' % (len(successes)))
        print('%% of successes: %s' % (float(len(successes)) / total_tests * 100))
        times = [d['total_time'] for d in data]
        print('Average time of process: %s' % (sum(times) / len(times)))
