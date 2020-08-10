# pragma: no cover
import csv

from dateutil.parser import parse

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.timezone import get_default_timezone

from genesishealth.apps.accounts.models import PatientProfile
from genesishealth.apps.orders.models import (
    Order, OrderCategory, OrderEntry, OrderShipment)
from genesishealth.apps.pharmacy.models import PharmacyPartner
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
        try:
            ship_date = tz.localize(parse(row[0]))
        except ValueError:
            raise ImportOrderHistoryException("No ship date")
        invoice_number = row[1]
        insurance_identifier = row[8]
        last_name = row[10]
        try:
            device_count = int(row[19])
        except ValueError:
            device_count = 0
        try:
            strip_count = int(row[20])
        except ValueError:
            strip_count = 0
        try:
            order_date = tz.localize(parse(row[21]))
        except ValueError:
            raise ImportOrderHistoryException("No order date")
        order_notes = row[22]

        order_kwargs = {
            'datetime_added': order_date,
            'order_status': Order.ORDER_STATUS_SHIPPED,
            'order_origin': Order.ORDER_ORIGIN_BATCH_IMPORT,
            'datetime_shipped': ship_date,
            'order_notes': order_notes
        }
        # Figure out if it's a bulk order or not
        is_bulk_order = invoice_number != ""
        if is_bulk_order:
            if last_name == "Gathright Reed Medical Supply":
                rx_partner = PharmacyPartner.objects.get(name="Gathright Reed")
            elif last_name == 'Vital Care of Meridian':
                rx_partner = PharmacyPartner.objects.get(name='Vital Care')
            elif last_name == 'Acaria Pharmacy':
                rx_partner = PharmacyPartner.objects.get(name='Acaria')
            else:
                raise ImportOrderHistoryException(
                    "Invalid RX Partner {0}".format(last_name))
            order_kwargs['rx_partner'] = rx_partner
            order_kwargs['order_type'] = Order.ORDER_TYPE_BULK
            order_kwargs['invoice_number'] = invoice_number
        else:
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
                order_kwargs['order_category'] = OrderCategory.objects.get(
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
        OrderShipment.objects.create(
            order=order,
            shipped_date=ship_date,
            packed_by=User.objects.get(pk=2419))
