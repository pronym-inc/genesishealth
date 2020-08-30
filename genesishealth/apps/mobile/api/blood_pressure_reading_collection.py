from typing import Type, Optional, Dict

from django.db.models import QuerySet
from pronym_api.models import ApiAccountMember
from pronym_api.views.actions import ResourceAction
from pronym_api.views.api_view import ResourceT, ActionT, HttpMethod

from pronym_api.views.model_view.views import ModelCollectionApiView

from genesishealth.apps.accounts.models import PatientProfile
from genesishealth.apps.blood_pressure.models import BloodPressureReading


class BloodPressureReadingCollectionApiView(ModelCollectionApiView[BloodPressureReading]):
    def _check_authorization(
            self,
            requester: ApiAccountMember,
            resource: Optional[BloodPressureReading],
            action: ResourceAction
    ) -> bool:
        try:
            requester.user.patient_profile
        except PatientProfile.DoesNotExist:
            return False
        return True

    def _get_model(self) -> Type[BloodPressureReading]:
        return BloodPressureReading

    def _get_queryset(self) -> 'QuerySet[BloodPressureReading]':
        return self.authenticated_account_member.user.patient_profile.blood_pressure_readings.all()
