import sys
import shlex
import subprocess
import re
import os

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle_noargs(self, **options):
        # Ascertain the amount of items in the queue.
        cmd = "sudo rabbitmqctl list_queues -p /genesishealth"
        output = subprocess.check_output(shlex.split(cmd))
        results = re.findall(r"\ncelery\t(\d+)\n", output)
        if not results:
            print("Could not determine queue status.")
            sys.exit(2)
        count = int(results[0])
        # Now look up previous.
        queue_file = '/tmp/queue_status'
        if os.path.exists(queue_file):
            # Check to see if the queue looks stalled.
            with open(queue_file) as f:
                contents = f.read()
                results = contents.split("\n")
                if count > 0:
                    error = all(map(lambda x: 0 < x <= count, results))
                else:
                    error = False
                results = [count] + results[:4]
        else:
            error = False
            results = [count]
        # Write results to file.
        with open(queue_file, 'w') as f:
            f.write("\n".join(map(str, results)))
        if error:
            print("Queue appears to be stuck.")
            sys.exit(2)
        else:
            sys.exit(0)
