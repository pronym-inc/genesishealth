import csv

from io import BytesIO

from dateutil.parser import parse

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from genesishealth.apps.epc.models import EPCOrder
from genesishealth.apps.reports.models import TemporaryDownload


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('source_files', type=str, nargs='*')

    def handle(self, *args, **options):
        recipient = User.objects.get(pk=2419)
        output_rows = []
        for file_path in options['source_files']:
            with open(file_path) as f:
                reader = csv.reader(f)
                # Skip header
                reader.next()
                line_number = 1
                for row in reader:
                    line_number += 1
                    order_number = row[0]
                    insurance_identifier = row[1]
                    order_status = row[2]
                    order = EPCOrder.objects.get(order_number=order_number)
                    profile = order.epc_member

                    if profile.insurance_identifier != insurance_identifier:
                        print(
                            "Mismatched insurance identifiers on "
                            "line {0}".format(line_number))
                        continue

                    if order_status == 'shipped':
                        ship_date = parse(row[6]).strftime('%Y%m%d')
                        mail_carrier = row[7]
                        tracking_number = row[8]

                        try:
                            strip_quantity = int(row[3])
                        except ValueError:
                            strip_quantity = 0

                        try:
                            meter_quantity = int(row[4])
                        except ValueError:
                            meter_quantity = 0

                        try:
                            lancet_quantity = int(row[5])
                        except ValueError:
                            lancet_quantity = 0

                        if meter_quantity > 0:
                            device = profile.get_device()
                            if device is None:
                                print(
                                    "Could not find MEID for patient"
                                    " on line {0}".format(line_number))
                                continue
                            meid = device.meid
                        else:
                            meid = ''
                    else:
                        meid = ship_date = mail_carrier = tracking_number = ''
                        strip_quantity = meter_quantity = lancet_quantity = 0

                    output_rows.append([
                        order_number,
                        '',  # claimID
                        profile.insurance_identifier,
                        meter_quantity,
                        strip_quantity,
                        lancet_quantity,
                        0,  # Lancing devices shipped
                        0,  # Control solution shipped
                        order_status,
                        ship_date,
                        tracking_number,
                        mail_carrier,
                        meid
                    ])
        # Create EPC pharmacy file
        headers = [
            'rhOrderNumber',
            'claimID',
            'insuranceID',
            'meterQtyShipped',
            'stripsQtyShipped',
            'lancetsQtyShipped',
            'lancingDevicesQtyShipped',
            'controlSolutionQtyShipped',
            'orderStatus',
            'shipDate',
            'trackingNumber',
            'carrier',
            'meid'
        ]

        buf = BytesIO()
        writer = csv.writer(buf)
        writer.writerow(headers)
        for row in output_rows:
            writer.writerow(row)

        buf.seek(0)

        TemporaryDownload.objects.create(
            for_user=recipient,
            content=buf.getvalue(),
            filename='epc_pharma_file.csv'
        )
