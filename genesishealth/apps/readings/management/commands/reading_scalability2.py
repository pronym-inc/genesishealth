import random
import socket
from importlib import import_module
from datetime import timedelta
from multiprocessing import Pool
from time import sleep

from django.core.management.base import BaseCommand
from django.utils.timezone import now

from .reading_scalability import new_process_remote


class Command(BaseCommand):

    help = (
        "Sends a reading to the specified reading servers at a specified rate."
    )

    def handle(self, readings_per_second, duration=None,
               environment_settings=None, max_processes=10, debug=False, *args,
               **options):
        if environment_settings:
            target_settings = import_module('genesishealth.conf.%s.settings' %
                                            environment_settings)
        else:
            from django.conf import settings as target_settings

        results = []
        max_processes = int(max_processes)
        readings_per_second = float(readings_per_second)
        pool = Pool(processes=max_processes)
        # Invert readings per second to figure out interval per reading
        interval = readings_per_second ** -1
        start_time = now()
        print("Sending a reading every {} seconds.".format(interval))
        count = 0
        duration = int(duration)
        if duration:
            end_time = now() + timedelta(seconds=duration)
        else:
            end_time = None
        while end_time is None or now() < end_time:
            try:
                meid, serial = random.choice(target_settings.SCALABILITY_DEVICES)
                print("Sending reading.")
                results.append(pool.apply_async(new_process_remote, (
                    random.choice(target_settings.READING_SERVER_LOCATIONS),
                    target_settings.GDRIVE_READING_PORT,
                    meid,
                    serial,
                    debug,
                    False
                )))
                count += 1
                sleep(interval)
            except KeyboardInterrupt:
                break
        # Let's finish up any lingering requests.
        data = []
        while True:
            new_results = []
            for result in results:
                if result.ready():
                    try:
                        r = result.get(timeout=3)
                    except socket.error:
                        pass
                    else:
                        data.append(r)
                        continue
                new_results.append(result)
            if len(new_results) == 0:
                break
            results = new_results
            sleep(0.1)
        stop_time = now()

        # Now make a report.
        print("Test start time: {}".format(start_time))
        print("Test end time: {}".format(stop_time))
        print("Test total time: {} minutes".format((stop_time - start_time).total_seconds() / 60))

        def get_average_processing_time(dataset):
            return float(sum([x['total_time'] for x in dataset])) / len(dataset)

        average = get_average_processing_time(data)
        length = len(data)
        first_20 = data[:int(length * 0.2)]
        average_first_20 = get_average_processing_time(first_20)
        middle_20 = data[int(length * 0.4):(length - int(length * 0.4))]
        average_middle_20 = get_average_processing_time(middle_20)
        last_20 = data[int(length * 0.8):]
        average_last_20 = get_average_processing_time(last_20)

        print("Average processing time for a reading: {}s".format(average))
        print("Average processing time first 20%: {}s".format(average_first_20))
        print("Average processing time middle 20%: {}s".format(average_middle_20))
        print("Average processing time last 20%: {}s".format(average_last_20))

        successful = filter(lambda x: x['success'], data)
        success_rate = float(len(successful)) / count
        print("Reading success rate: {}%").format(success_rate * 100)
