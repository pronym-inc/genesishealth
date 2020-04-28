# pragma: no cover
import csv

from dateutil.parser import parse

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.timezone import get_default_timezone

from genesishealth.apps.accounts.models import PatientProfile
from genesishealth.apps.orders.models import (
    Order, OrderCategory, OrderEntry, OrderShipment)
from genesishealth.apps.products.models import ProductType


class ImportOrderHistoryException(Exception):
    pass


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('history_file_path', type=str)

    def handle(self, *args, **options):
        with open(options['history_file_path']) as f:
            reader = csv.reader(f)
            # Skip header.
            reader.next()
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
        try:
            ship_date = tz.localize(parse(row[18]))
        except ValueError:
            ship_date = None
        insurance_identifier = row[3]
        try:
            device_count = int(row[14])
        except ValueError:
            device_count = 0
        try:
            strip_count = int(row[15])
        except ValueError:
            strip_count = 0
        try:
            order_date = tz.localize(parse(row[1]))
        except ValueError:
            raise ImportOrderHistoryException("No order date")

        if ship_date is None:
            order_status = Order.ORDER_STATUS_IN_PROGRESS
        else:
            order_status = Order.ORDER_STATUS_SHIPPED

        order_kwargs = {
            'datetime_added': order_date,
            'order_status': order_status,
            'order_origin': Order.ORDER_ORIGIN_BATCH_IMPORT,
            'datetime_shipped': ship_date
        }
        # Find patient
        try:
            profile = PatientProfile.objects.get(
                insurance_identifier=insurance_identifier)
        except PatientProfile.DoesNotExist:
            raise ImportOrderHistoryException(
                "No patient found with insurance identifier: {0}".format(
                    insurance_identifier))
        except PatientProfile.MultipleObjectsReturned:
            raise ImportOrderHistoryException(
                "Multiple profiles found with insurance id {0}".format(
                    insurance_identifier))
        order_kwargs['patient'] = profile.user
        order_kwargs['order_type'] = Order.ORDER_TYPE_PATIENT
        if strip_count > 0:
            order_kwargs['category'] = OrderCategory.objects.get(
                is_refill=True)

        order = Order.objects.create(**order_kwargs)
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
        if ship_date is not None:
            OrderShipment.objects.create(
                order=order,
                shipped_date=ship_date,
                packed_by=User.objects.get(pk=2419))
