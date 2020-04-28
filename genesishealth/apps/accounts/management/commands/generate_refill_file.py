import csv

from datetime import timedelta
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
        parser.add_argument('user_id', type=int)
        parser.add_argument('start_date', type=str, nargs='?', default='')
        parser.add_argument('end_date', type=str, nargs='?', default='')

    def handle(self, *args, **options):
        recipient = User.objects.get(pk=options['user_id'])
        tz = get_default_timezone()
        if options['start_date']:
            start_date = parse(options['start_date'])
        else:
            start_date = (
                now() - timedelta(days=1)
            ).astimezone(tz).date()
        if options['end_date']:
            end_date = parse(options['end_date'])
            filter_kwargs = {
                'order_date__range': (start_date, end_date)
            }
        else:
            end_date = None
            filter_kwargs = {'order_date': start_date}

        headers = [
            'ORDER NUMBER',
            'INSURANCEID',
            'FIRSTNAME',
            'MIDDLEINITIAL',
            'LASTNNAME',
            'DOB',
            'ADDRESS1',
            'ADDRESS2',
            'CITY',
            'STATE',
            'ZIP',
            'PHONE',
            'STRIPS QUANTITY',
            'METER QUANTITY',
            'PHARMACY'
        ]
        date_format = "%Y_%m_%d"

        for group in GenesisGroup.objects.filter(
                should_generate_refill_files=True):
            group_filter_kwargs = filter_kwargs.copy()
            group_filter_kwargs['epc_member__group'] = group
            orders = EPCOrder.objects.filter(**group_filter_kwargs)
            cleaned_group_name = group.name.lower().replace(' ', '_')
            if end_date:
                filename = "{0}_{1}_{2}_orders.csv".format(
                    cleaned_group_name,
                    start_date.strftime(date_format),
                    end_date.strftime(date_format)
                )
            else:
                filename = "{0}_{1}_orders.csv".format(
                    cleaned_group_name,
                    start_date.strftime(date_format)
                )
            buf = BytesIO()
            writer = csv.writer(buf)
            writer.writerow(headers)
            for order in orders:
                profile = order.epc_member
                user = profile.user
                contact = profile.contact
                writer.writerow([
                    order.order_number,
                    profile.insurance_identifier,
                    user.first_name,
                    '',
                    user.last_name,
                    profile.date_of_birth,
                    contact.address1,
                    contact.address2,
                    contact.city,
                    contact.state,
                    contact.zip,
                    contact.phone,
                    order.strips_request,
                    order.meter_request,
                    'GHT'
                ])
            buf.seek(0)
            TemporaryDownload.objects.create(
                for_user=recipient,
                content=buf.getvalue(),
                filename=filename)
