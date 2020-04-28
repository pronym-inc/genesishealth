from json import loads

from django.core.management.base import BaseCommand

from genesishealth.apps.reports.tasks import run_report_async


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('report_name', type=str)
        parser.add_argument('form_data', type=str)
        parser.add_argument('form_config', type=str)
        parser.add_argument('recipient_id', type=int)

    def handle(self, *args, **options):
        form_data = loads(options['form_data'])
        form_config = loads(options['form_config'])
        run_report_async.delay(
            options['report_name'],
            options['recipient_id'],
            form_data,
            form_config
        )
