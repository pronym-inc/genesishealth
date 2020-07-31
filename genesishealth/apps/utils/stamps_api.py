from datetime import date
from typing import List, Optional

from django.conf import settings
from stamps.request_models.common import StampsAddress, Rate, PackageType
from stamps.response_models.create_indicium import PostageLabel
from stamps.service import StampsService


class GenesisStampsService:
    _service: StampsService

    def __init__(self):
        self._service = self._get_service()

    def cleanse_address(self, address: StampsAddress) -> Optional[StampsAddress]:
        return self._service.cleanse_address(address)

    def get_label(
            self,
            to_address: StampsAddress,
            rate: Rate
    ) -> Optional[PostageLabel]:
        from_address = StampsAddress(
            first_name=settings.STAMPS_FROM_ADDRESS['FullName'].split(' ')[0],
            last_name=' '.join(settings.STAMPS_FROM_ADDRESS['FullName'].split(' ')[1:]),
            address=settings.STAMPS_FROM_ADDRESS['Address1'],
            address2=settings.STAMPS_FROM_ADDRESS['Address2'],
            city=settings.STAMPS_FROM_ADDRESS['City'],
            state=settings.STAMPS_FROM_ADDRESS['State'],
            zipcode=settings.STAMPS_FROM_ADDRESS['ZipCode']
        )
        return self._service.get_label(to_address, from_address, rate)

    def get_rates(
            self,
            to_zip: str,
            weight_in_ounces: float,
            ship_date: date,
            package_type: PackageType,
    ) -> Optional[List[Rate]]:
        from_zip = settings.STAMPS_FROM_ADDRESS['ZipCode']
        print(ship_date)
        print(from_zip)
        print(to_zip)
        return self._service.get_rates(from_zip, to_zip, weight_in_ounces, ship_date, package_type)

    @classmethod
    def _get_service(cls) -> StampsService:
        return StampsService(
            integration_id=settings.STAMPS_INTEGRATION_ID,
            username=settings.STAMPS_USERNAME,
            password=settings.STAMPS_PASSWORD,
            is_dev=settings.STAMPS_USE_DEV_SERVER
        )
