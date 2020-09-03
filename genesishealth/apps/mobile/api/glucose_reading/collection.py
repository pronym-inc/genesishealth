from typing import Type, Dict, Optional

from django.db.models import QuerySet

from pronym_api.models import ApiAccountMember
from pronym_api.views.actions import ResourceAction
from pronym_api.views.api_view import HttpMethod
from pronym_api.views.model_view.views import ModelCollectionApiView

from genesishealth.apps.accounts.models import PatientProfile
from genesishealth.apps.readings.models import GlucoseReading


class GlucoseReadingCollectionApiView(ModelCollectionApiView[GlucoseReading]):
    def _check_authorization(
            self,
            requester: ApiAccountMember,
            resource: Optional[GlucoseReading],
            action: ResourceAction
    ) -> bool:
        try:
            requester.user.patient_profile
        except PatientProfile.DoesNotExist:
            return False
        return True

    def _get_action_configuration(self) -> Dict[HttpMethod, ResourceAction]:
        config = super()._get_action_configuration()
        del config[HttpMethod.POST]
        return config

    def _get_model(self) -> Type[GlucoseReading]:
        return GlucoseReading

    def _get_queryset(self) -> 'QuerySet[GlucoseReading]':
        return self.authenticated_account_member.user.glucose_readings.order_by('-reading_datetime_utc')
