from time import sleep
from importlib import import_module
import random

from django.core.management.base import BaseCommand

from .reading_scalability import new_process_remote


class Command(BaseCommand):
    def handle(self, environment_settings=None, check_every=5, *args, **options):
        if environment_settings:
            target_settings = import_module('genesishealth.conf.%s.settings' % environment_settings)
        else:
            from django.conf import settings as target_settings
        results = []
        times = []
        successes = 0
        server_times = {host: [] for host in target_settings.READING_SERVER_LOCATIONS}
        server_max_times = {host: 0 for host in target_settings.READING_SERVER_LOCATIONS}
        max_time = 0
        check_every = int(check_every)
        while True:
            try:
                meid, serial = random.choice(target_settings.SCALABILITY_DEVICES)
                server = random.choice(target_settings.READING_SERVER_LOCATIONS)
                new_result = new_process_remote(
                    server,
                    target_settings.GDRIVE_READING_PORT,
                    meid, serial, True
                )
                new_time = new_result['total_time']
                results.append(new_result)
                times.append(new_time)
                server_times[server].append(new_time)
                if new_time > max_time:
                    max_time = new_time
                if new_time > server_max_times[server]:
                    server_max_times[server] = new_time
                if new_result['success']:
                    successes += 1
                average_time = float(sum(times)) / len(times)
                success_rate = float(successes) / len(results)
                print("Total tests: {}".format(len(results)))
                print("Average time: {}".format(average_time))
                print("Success rate: {}%".format(success_rate * 100))
                last_20 = times[-20:]
                average_time_last_20 = float(sum(last_20)) / min(len(last_20), 20)
                print("Average time last 20: {}".format(average_time_last_20))
                print("Max time: {}".format(max_time))

                for host, s_times in server_times.items():
                    if s_times:
                        avg = float(sum(s_times)) / len(s_times)
                        print("{} Average Time: {}".format(host, avg))
                        print("{} Max time: {}".format(host, server_max_times[host]))
                sleep(check_every)
            except KeyboardInterrupt:
                break
