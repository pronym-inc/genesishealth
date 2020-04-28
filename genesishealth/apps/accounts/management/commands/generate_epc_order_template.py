import csv

from io import BytesIO

from dateutil.parser import parse

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.timezone import get_default_timezone, now

from genesishealth.apps.accounts.models import GenesisGroup
from genesishealth.apps.epc.models import EPCOrder
from genesishealth.apps.reports.models import TemporaryDownload


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('start_date', type=str, nargs='?', default='')
        parser.add_argument('end_date', type=str, nargs='?', default='')

    def handle(self, *args, **options):
        recipient_id = 2419
        recipient = User.objects.get(pk=recipient_id)
        tz = get_default_timezone()
        if options['start_date']:
            start_date = parse(options['start_date'])
        else:
            start_date = now().astimezone(tz).date()
        if options['end_date']:
            end_date = parse(options['end_date'])
            filter_kwargs = {
                'order_date__range': (start_date, end_date)
            }
        else:
            end_date = None
            filter_kwargs = {'order_date': start_date}

        headers = [
            'order number',
            'insurance id',
            'status',
            'strips',
            'meters',
            'lancets',
            'ship date',
            'mail carrier',
            'tracking number'
        ]
        date_format = "%Y_%m_%d"

        buf = BytesIO()
        writer = csv.writer(buf)
        writer.writerow(headers)

        for group in GenesisGroup.objects.filter(
                should_generate_refill_files=True):
            group_filter_kwargs = filter_kwargs.copy()
            group_filter_kwargs['epc_member__group'] = group
            orders = EPCOrder.objects.filter(**group_filter_kwargs)
            for order in orders:
                profile = order.epc_member
                writer.writerow([
                    order.order_number,
                    profile.insurance_identifier
                ])
        # Create the file
        buf.seek(0)
        if end_date:
            filename = "{0}_{1}_order_template.csv".format(
                start_date.strftime(date_format),
                end_date.strftime(date_format)
            )
        else:
            filename = "{0}_order_template.csv".format(
                start_date.strftime(date_format)
            )
        TemporaryDownload.objects.create(
            for_user=recipient,
            content=buf.getvalue(),
            filename=filename)
