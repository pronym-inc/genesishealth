from typing import Type, Dict, Optional, Any, Union

from django.db.models import QuerySet

from pronym_api.models import ApiAccountMember
from pronym_api.views.actions import ResourceAction, ApiProcessingFailure
from pronym_api.views.api_view import HttpMethod
from pronym_api.views.model_view.actions.search import SearchModelResourceAction
from pronym_api.views.model_view.views import ModelCollectionApiView

from genesishealth.apps.accounts.models import PatientProfile
from genesishealth.apps.readings.models import GlucoseReading


class SearchGlucoseReadingResourceAction(SearchModelResourceAction[GlucoseReading]):
    def execute(self, request: Dict[str, Any], account_member: Optional[ApiAccountMember],
                resource: 'QuerySet[GlucoseReading]') -> Optional[Union[ApiProcessingFailure, Dict[str, Any]]]:
        return {
            "results": [
                {
                    "reading_datetime_utc": reading.reading_datetime_utc,
                    "glucose_value": reading.glucose_value
                }
                for reading in resource
            ]
        }


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
        return {
            HttpMethod.GET: SearchGlucoseReadingResourceAction()
        }

    def _get_model(self) -> Type[GlucoseReading]:
        return GlucoseReading

    def _get_queryset(self) -> 'QuerySet[GlucoseReading]':
        return self.authenticated_account_member.user.glucose_readings.order_by('-reading_datetime_utc')
