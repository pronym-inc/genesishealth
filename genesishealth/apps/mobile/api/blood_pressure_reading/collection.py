from typing import Type, Optional, Dict, Any

from django.db.models import QuerySet
from pronym_api.models import ApiAccountMember
from pronym_api.views.actions import ResourceAction
from pronym_api.views.api_view import HttpMethod
from pronym_api.views.model_view.actions.create import CreateModelResourceAction
from pronym_api.views.model_view.modelform import LazyModelForm
from pronym_api.views.model_view.views import ModelCollectionApiView

from genesishealth.apps.accounts.models import PatientProfile
from genesishealth.apps.blood_pressure.models import BloodPressureReading


class CreateBloodPressureReadingAction(CreateModelResourceAction[BloodPressureReading]):
    def _save_form(self, form: LazyModelForm, request: Dict[str, Any], account_member: Optional[ApiAccountMember],
                   resource: BloodPressureReading) -> BloodPressureReading:
        obj: BloodPressureReading = super(CreateBloodPressureReadingAction, self)._save_form(
            form, request, account_member, resource)
        if account_member is not None:
            obj.patient_profile = account_member.user.patient_profile
            obj.save()
        return obj


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

    def _get_action_configuration(self) -> Dict[HttpMethod, ResourceAction]:
        config = super()._get_action_configuration()
        config[HttpMethod.POST] = CreateBloodPressureReadingAction(self._get_model())
        return config

    def _get_model(self) -> Type[BloodPressureReading]:
        return BloodPressureReading

    def _get_queryset(self) -> 'QuerySet[BloodPressureReading]':
        return self\
            .authenticated_account_member\
            .user\
            .patient_profile\
            .blood_pressure_readings\
            .order_by('-datetime_received')
