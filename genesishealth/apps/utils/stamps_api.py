from datetime import date
from typing import List, Optional

from django.conf import settings
from stamps.request_models.common import StampsAddress, Rate, ServiceType, PackageType
from stamps.response_models.create_indicium import PostageLabel
from stamps.service import FakeStampsService, BaseStampsService, StampsService


class GenesisStampsService:
    _service: BaseStampsService

    def __init__(self):
        self._service = self._get_service()

    def cleanse_address(self, address: StampsAddress) -> StampsAddress:
        return self._service.cleanse_address(address)

    def get_label(
            self,
            to_address: StampsAddress,
            from_address: StampsAddress,
            rate: Rate
    ) -> PostageLabel:
        return self._service.get_label(to_address, from_address, rate)

    def get_rates(
            self,
            from_zip: str,
            to_zip: str,
            weight_in_ounces: float,
            ship_date: date,
            package_type: PackageType,
    ) -> List[Rate]:
        return self._service.get_rates(from_zip, to_zip, weight_in_ounces, ship_date, package_type)

    @classmethod
    def _get_service(cls) -> BaseStampsService:
        if settings.STAMPS_USE_FAKE_SERVICE:
            return FakeStampsService(settings.STAMPS_FAKE_LABEL_URL)
        else:
            return StampsService(
                integration_id=settings.STAMPS_INTEGRATION_ID,
                username=settings.STAMPS_USERNAME,
                password=settings.STAMPS_PASSWORD,
                is_dev=settings.STAMPS_USE_DEV_SERVER
            )
