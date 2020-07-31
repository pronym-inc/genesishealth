import logging
from typing import List, Optional

import typing
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now
from stamps.request_models.common import Rate, PackageType, ServiceType, StampsAddress
from stamps.response_models.create_indicium import PostageLabel

from genesishealth.apps.orders.models.shipping_class import ShippingClass
from genesishealth.apps.utils.stamps_api import GenesisStampsService

if typing.TYPE_CHECKING:
    from genesishealth.apps.accounts.models import Contact

logger = logging.getLogger(__name__)


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

    def create_shipping_label(self) -> Optional[PostageLabel]:
        """Try to create a shipping label for this order."""
        service = GenesisStampsService()
        rates = self.get_shipping_rates()
        if rates is None or len(rates) == 0:
            logger.warning("No rate found!")
            return None
        rate = rates[0]
        patient: User = self.order.patient
        contact: 'Contact' = patient.patient_profile.contact
        clean_to_address = service.cleanse_address(StampsAddress(
            first_name=self.order.patient.first_name,
            last_name=self.order.patient.last_name,
            address=contact.address1,
            address2=contact.address2,
            city=contact.city,
            state=contact.state,
            zipcode=contact.zip
        ))
        return service.get_label(
            to_address=clean_to_address,
            rate=rate
        )

    def finalize(self, shipped_by: Optional[User] = None) -> None:
        self.shipped_date = now().date()
        self.shipped_by = shipped_by
        self.is_finalized = True
        label = self.create_shipping_label()
        self.tracking_number = label.tracking_number
        self.shipping_label_url = label.url
        self.save()
        self.order.check_if_shipped()

    def get_shipping_rates(self, get_all: bool = False) -> Optional[List[Rate]]:
        address_data = self.order.get_shipping_address()
        service = GenesisStampsService()
        returned_rates = service.get_rates(
            to_zip=address_data['zip'],
            package_type=PackageType.PACKAGE,
            ship_date=self.shipped_date,
            weight_in_ounces=self.weight_pounds * 16 + self.weight_ounces
        )
        if returned_rates is None:
            return None
        allowable_service_types: List[ServiceType]
        if get_all:
            allowable_service_types = list(map(
                lambda x: ServiceType(x.stamps_abbreviation),
                ShippingClass.objects.filter(enabled=True)
            ))
        elif self.shipping_class is None:
                allowable_service_types = []
        else:
            allowable_service_types = [ServiceType(self.shipping_class.stamps_abbreviation)]
        return list(filter(
            lambda x: x.service_type in allowable_service_types,
            returned_rates
        ))
