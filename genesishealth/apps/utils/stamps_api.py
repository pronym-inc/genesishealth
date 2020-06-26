from datetime import date

from django.conf import settings
from stamps.config import StampsConfiguration
from stamps.services import StampsService


def create_stamps_connection() -> StampsService:
    configuration = StampsConfiguration(
        integration_id=settings.STAMPS_INTEGRATION_ID,
        username=settings.STAMPS_USERNAME,
        password=settings.STAMPS_PASSWORD
    )
    service = StampsService(configuration=configuration)
    return service


def create_stamps_label(
        from_address: str,
        to_address: str,
        rate_info, package_type,
        hide_postage=True, connection=None):
    connection = connection if connection else create_stamps_connection()
    rate = connection.create_shipping()
    rate.ShipDate = date.today().isoformat()
    rate.FromZIPCode = from_address.ZIPCode
    rate.ToZIPCode = to_address.ZIPCode
    rate.PackageType = package_type
    copy_fields = ('Amount', 'ServiceType', 'DeliverDays', 'DimWeighting',
                   'Zone', 'RateCategory', 'ToState')
    for field in copy_fields:
        setattr(rate, field, getattr(rate_info, field))
    if hide_postage:
        add_on = connection.create_add_on()
        add_on.AddOnType = "SC-A-HP"
        rate.AddOns.AddOnV7.append(add_on)
    transaction_id = date.today().isoformat()
    return connection.get_label(
        from_address, to_address, rate, transaction_id=transaction_id)


def get_rates(rate_names, shipment_data, connection=None):
    """shipment_data, e.g.
    shipment_data = {
    'FromZIPCode': '94107', 'ToZIPCode': '20500', 'PackageType': 'Package',
    'ShipDate': date.today ().isoformat()}"""
    connection = connection if connection else create_stamps_connection()
    shipping_obj = connection.create_shipping()
    for key, value in shipment_data.items():
        setattr(shipping_obj, key, value)
    rates = connection.get_rates(shipping_obj)
    return filter(lambda x: x.ServiceType in rate_names, rates)


def get_stamps_address(address_data, connection=None):
    """Address data, e.g.
    {"FullName": "POTUS", "Address1": "1600 Pennsylvania Avenue NW",
    "City": "Washington", "State": "DC"}"""
    connection = connection if connection else create_stamps_connection()
    address = connection.create_address()
    fields = ('FullName', 'Address1', 'Address2', 'City', 'State')
    for field in fields:
        if field in address_data:
            setattr(address, field, address_data[field])
    return connection.get_address(address).Address
