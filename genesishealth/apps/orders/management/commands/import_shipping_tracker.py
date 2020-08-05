# pragma: no cover
import csv
import logging
from datetime import timedelta
from typing import List

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
    def add_arguments(self, parser) -> None:
        parser.add_argument('tracker_file_path', type=str)
        parser.add_argument('--dry-run', dest='dry-run', action='store_true')

    def handle(self, *args, **options) -> None:
        with open(options['tracker_file_path']) as f:
            reader = csv.reader(f)
            # Skip header.
            next(reader)
            counter = 0
            for row in reader:
                counter += 1
                self.process_row(row, counter, options['dry-run'])

    def process_row(self, row: List[str], row_count: int, dry_run: bool) -> None:
        tz = get_default_timezone()

        insurance_identifier = row[2]
        try:
            profile = PatientProfile.objects.get(insurance_identifier=insurance_identifier)
        except PatientProfile.DoesNotExist:
            logger.warning(
                f"[{row_count}] Could not find patient with insurance identifier {insurance_identifier}, skipping."
            )
            return

        try:
            order_date = ship_date = tz.localize(parse(row[3]))
        except ValueError:
            logger.warning(f"[{row_count}] Couldn't parse a last refill date: {row[3]}, skipping.")
            return

        # See if we have a refill within a day of it.
        start = order_date - timedelta(days=2)
        end = order_date + timedelta(days=2)
        if len(profile.user.orders.filter(datetime_shipped__range=(start, end), category__is_refill=True)) > 0:
            logger.warning(f"[{row_count}] Found refill order within a few days, skipping.")
            return

        try:
            strip_count = int(row[4]) // 50
        except ValueError:
            logger.warning(f"[{row_count}] Could not parse strip amount: {row[4]}")
            return

        order_category = OrderCategory.objects.get(name='Automatic Refill')
        order_type = Order.ORDER_TYPE_PATIENT

        if dry_run:
            print(
                f"Would create new order with {strip_count} strips for {profile.user.first_name} "
                f"{profile.user.last_name} for date {order_date}"
            )
        else:
            order = Order.objects.create(
                patient=profile.user,
                order_type=order_type,
                category=order_category,
                datetime_added=order_date,
                order_status=Order.ORDER_STATUS_SHIPPED,
                order_origin=Order.ORDER_ORIGIN_BATCH_IMPORT,
                datetime_shipped=ship_date
            )
            # Add entries
            if strip_count > 0:
                OrderEntry.objects.create(
                    order=order,
                    quantity=strip_count,
                    product=ProductType.objects.get(category=ProductType.CATEGORY_STRIPS))
            # Create the shipment
            OrderShipment.objects.create(
                order=order,
                shipped_date=ship_date
            )
