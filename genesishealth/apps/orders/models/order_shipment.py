from django.conf import settings
from django.db import models
from django.utils.timezone import now

from genesishealth.apps.orders.models.shipping_class import ShippingClass
from genesishealth.apps.utils.stamps_api import (
    create_stamps_connection, create_stamps_label,
    get_rates, get_stamps_address)


class OrderShipment(models.Model):
    SHIPPING_CLASS_PRIORITY = 'priority'

    SHIPPING_CLASS_CHOICES = (
        (SHIPPING_CLASS_PRIORITY, 'Priority'),
    )

    SHIPPING_PIECE_BOX = 'box'

    SHIPPING_PIECE_CHOICES = (
        (SHIPPING_PIECE_BOX, 'Box'),
    )

    SHIP_VENDOR_UPS = 'ups'

    SHIP_VENDOR_CHOICES = (
        (SHIP_VENDOR_UPS, 'UPS'),
    )

    order = models.ForeignKey('Order', related_name='shipments', on_delete=models.CASCADE)
    shipping_class = models.ForeignKey('ShippingClass', null=True, on_delete=models.SET_NULL)
    package_type = models.ForeignKey('ShippingPackageType', null=True, on_delete=models.SET_NULL)
    package_length = models.FloatField(null=True)
    package_height = models.FloatField(null=True)
    package_width = models.FloatField(null=True)
    packed_date = models.DateField(null=True)
    packed_by = models.ForeignKey(
        'auth.User', related_name="order_shipments_packed", null=True, on_delete=models.SET_NULL)
    shipped_date = models.DateField(default=now)
    shipped_by = models.ForeignKey(
        'auth.User', related_name="orders_shipped", null=True, on_delete=models.SET_NULL)
    ship_vendor = models.CharField(
        max_length=255, choices=SHIP_VENDOR_CHOICES)
    tracking_number = models.CharField(max_length=255, null=True)
    pharmacy_partner = models.ForeignKey(
        'pharmacy.PharmacyPartner', null=True, related_name='shipments', on_delete=models.SET_NULL)
    address_validated = models.BooleanField(default=False)
    shipping_label_url = models.TextField()
    is_finalized = models.BooleanField(default=False)
    weight_pounds = models.FloatField(null=True)
    weight_ounces = models.FloatField(null=True)

    def create_shipping_label(self, connection=None):
        if settings.DISABLE_STAMPS_LABELS:
            return
        connection = connection if connection else create_stamps_connection()
        rate_name = self.shipping_class.stamps_abbreviation
        rates = self.get_shipping_rates(connection=connection)
        if len(rates) == 0:
            raise Exception("No rate found with name {0}".format(rate_name))
        rate = rates[0]
        from_address = get_stamps_address(
            settings.STAMPS_FROM_ADDRESS, connection=connection)
        address_data = self.order.get_shipping_address()
        address_info = {
            'FullName': address_data['name'],
            'Address1': address_data['address1'],
            'City': address_data['city'],
            'State': address_data['state'],
            'ZipCode': address_data['zip']
        }
        if address_data.get('address2'):
            address_info['Address2'] = address_data['address2']
        to_address = get_stamps_address(address_info, connection=connection)
        return create_stamps_label(
            from_address,
            to_address,
            rate,
            self.package_type,
            connection=connection)

    def finalize(self, shipped_by=None, stamps_connection=None):
        stamps_connection = (
            stamps_connection if stamps_connection is not None else
            create_stamps_connection())
        self.shipped_date = now().date()
        self.shipped_by = shipped_by
        self.is_finalized = True
        label = self.create_shipping_label(stamps_connection)
        self.tracking_number = label.TrackingNumber
        self.shipping_label_url = label.URL
        self.save()
        self.order.check_if_shipped()

    def get_shipping_rates(self, get_all=False, connection=None):
        ship_date = (
            self.shipped_date if self.shipped_date is not None
            else now().date().isoformat())
        address_data = self.order.get_shipping_address()
        shipping_data = {
            'FromZIPCode': settings.STAMPS_FROM_ZIPCODE,
            'ToZIPCode': address_data['zip'],
            'PackageType': self.package_type.name,
            'WeightLb': self.weight_pounds,
            'WeightOz': self.weight_ounces,
            'ShipDate': ship_date
        }
        if get_all:
            allowable_names = list(map(
                lambda x: x.stamps_abbreviation,
                ShippingClass.objects.filter(enabled=True)))
        else:
            allowable_names = [self.shipping_class.stamps_abbreviation]
        return get_rates(
            allowable_names,
            shipping_data,
            connection=connection)
