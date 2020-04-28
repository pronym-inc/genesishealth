# pragma: no cover
import csv

from dateutil.parser import parse

from django.core.management.base import BaseCommand
from django.utils.timezone import get_default_timezone

from genesishealth.apps.accounts.models import PatientProfile


class Command(BaseCommand):
    help = \
        'Converts a Genesis formatted shipping history dump to a dump for EPC'

    def add_arguments(self, parser):
        parser.add_argument('history_file_path', type=str)
        parser.add_argument('output_path', type=str)

    def handle(self, *args, **options):
        tz = get_default_timezone()

        meter_ndc = 'unknown'
        strips_ndc = 'unknown'
        order_status = 'SHIPPED'
        order_trigger = 'UNKNOWN'
        order_type_map = {
            'InitialFiill': 'NEW',
            'Early Refill': 'REFILL',
            '90DayRefill': 'REFILL',
            'Begin or Restart Autofill': 'REFILL'
        }

        with open(options['history_file_path']) as f:
            rows = []
            rdr = csv.reader(f)
            # Skip header line
            rdr.next()
            # Go through rows and make new rows.
            for row in rdr:
                meter_count = int(row[19])
                strips_count = int(row[20])
                if meter_count == 0 and strips_count == 0:
                    continue
                insurance_id = row[8]
                ordered_on_date = tz.localize(parse(row[21]))
                ordered_on = ordered_on_date.strftime("%Y-%m-%dT00:00:00.000")
                shipped_on = tz.localize(
                    parse(row[0])).strftime("%Y-%m-%dT00:00:00.000")

                order_type = order_type_map.get(row[18], 'REPLACEMENT')

                # Look up patient
                try:
                    profile = PatientProfile.objects.get(
                        insurance_identifier=insurance_id)
                except PatientProfile.DoesNotExist:
                    print("Missing patient with id: {0}".format(insurance_id))
                    continue

                if meter_count > 0:
                    try:
                        device = profile.user.gdrives.filter(
                            datetime_assigned__gt=ordered_on_date).order_by(
                            'datetime_assigned')[0]
                    except IndexError:
                        print("Missing device for patient....{0}".format(
                            insurance_id))
                        continue
                    meid = device.meid
                else:
                    meid = ''

                new_row = [
                    insurance_id,
                    0,  # Control solution
                    0,  # Control soltion shipped
                    0,  # Lancets
                    0,  # Lancets shipped
                    0,  # Lancing devices
                    0,  # Lancing devices shipped
                    meter_count,  # Meters
                    meter_count,  # Meters shipped
                    meter_ndc,
                    ordered_on,
                    shipped_on,
                    order_status,
                    order_trigger,
                    order_type,
                    strips_count,
                    strips_count,
                    strips_ndc,
                    meid
                ]

                rows.append(new_row)

        with open(options['output_path'], 'w') as f:
            wtr = csv.writer(f)
            wtr.writerow([
                'insuranceID',
                'controlSolution',
                'controlSolutionQtyShipped',
                'lancets',
                'lancetsQtyShipped',
                'lancingDevices',
                'lancingDevicesShipped',
                'meter',
                'meterQtyShipped',
                'meterDNC',
                'orderedOn',
                'shippedOn',
                'orderStatus',
                'orderTrigger',
                'orderType',
                'strips',
                'stripsQtyShipped',
                'stripsNDC',
                'Meid'
            ])
            for row in rows:
                wtr.writerow(row)

        print("Wrote {0} records.".format(len(rows)))
