# pragma: no cover
import csv
import logging
from typing import Optional

from dateutil.parser import parse

from django.core.management.base import BaseCommand
from django.utils.timezone import get_default_timezone

from genesishealth.apps.accounts.models import PatientProfile
from genesishealth.apps.orders.models import (
    Order, OrderCategory, OrderEntry, OrderShipment)
from genesishealth.apps.products.models import ProductType


logger = logging.getLogger('import_order_history')


class ImportOrderHistoryException(Exception):
    pass


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('history_file_path', type=str)

    def handle(self, *args, **options):
        with open(options['history_file_path']) as f:
            reader = csv.reader(f)
            # Skip header.
            next(reader)
            counter = 0
            for row in reader:
                counter += 1
                try:
                    self.process_row(row)
                except ImportOrderHistoryException as e:
                    print("[{0}] Error - {1} - {2}".format(
                        counter,
                        str(e),
                        row))

    def process_row(self, row):
        tz = get_default_timezone()
        # If it has an invoice number, skip it - we're just interested in patient readings.
        invoice_number: Optional[str] = row[1] if len(row[1]) > 0 else None

        insurance_identifier = row[6]
        try:
            profile = PatientProfile.objects.get(insurance_identifier=insurance_identifier)
        except (PatientProfile.DoesNotExist, PatientProfile.MultipleObjectsReturned):
            logger.warning(f"Could not find patient with insurance ID: {insurance_identifier}, skipping...")
            return

        try:
            strip_count = int(row[18])
        except ValueError:
            logger.warning(f"Found non-integer value in strip column: {row[18]}, defaulting to 0")
            strip_count = 0

        if strip_count > 0:
            order_category = OrderCategory.objects.get(is_refill=True)
        else:
            order_category = None

        try:
            order_date = tz.localize(parse(row[19]))
        except ValueError:
            logger.warning(f"Could not parse order date: {row[19]}, skipping.")
            return

        try:
            ship_date = tz.localize(parse(row[0]))
        except ValueError:
            logger.warning(f"Could not parse ship date: {row[0]}, skipping.")
            return

        try:
            device_count = int(row[17])
        except ValueError:
            logger.warning(f"Could not parse device quantity: {row[17]}, skipping.")
            return

        order_type = Order.ORDER_TYPE_BULK if invoice_number is not None else Order.ORDER_TYPE_PATIENT

        order = Order.objects.create(
            patient=profile.user,
            order_type=order_type,
            category=order_category,
            datetime_added=order_date,
            order_status=Order.ORDER_STATUS_SHIPPED,
            order_origin=Order.ORDER_ORIGIN_BATCH_IMPORT,
            datetime_shipped=ship_date,
            order_notes=row[20],
            invoice_number=invoice_number
        )
        # Add entries
        if device_count > 0:
            OrderEntry.objects.create(
                order=order,
                quantity=device_count,
                product=ProductType.objects.get(
                    category=ProductType.CATEGORY_GDRIVE))
        if strip_count > 0:
            OrderEntry.objects.create(
                order=order,
                quantity=strip_count,
                product=ProductType.objects.get(
                    category=ProductType.CATEGORY_STRIPS))
        # Create the shipment
        OrderShipment.objects.create(
            order=order,
            shipped_date=ship_date
        )
