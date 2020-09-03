from typing import Dict, Any, Optional, Union

from pronym_api.models import ApiAccountMember
from pronym_api.views.actions import NoResourceAction, NullResource, ApiProcessingFailure
from pronym_api.views.api_view import HttpMethod, NoResourceApiView
from pronym_api.views.validation import ApiValidationErrorSummary


class GetMyProfileAction(NoResourceAction):
    def execute(self, request: Dict[str, Any], account_member: Optional[ApiAccountMember],
                resource: NullResource = NullResource()) -> Optional[Union[ApiProcessingFailure, Dict[str, Any]]]:
        if account_member is not None:
            output = {
                "first_name": account_member.user.first_name,
                "last_name": account_member.user.last_name,
                "address1": account_member.user.patient_profile.contact.address1,
                "address2": account_member.user.patient_profile.contact.address2,
                "city": account_member.user.patient_profile.contact.city,
                "state": account_member.user.patient_profile.contact.state,
                "zip_code": account_member.user.patient_profile.contact.zip,
            }
            maybe_device = account_member.user.patient_profile.get_device()
            if maybe_device:
                output['glucose_device'] = {
                    'meid': maybe_device.meid
                }
            output['blood_pressure_device'] = {
                'serial_number': 'ABC12312424124'
            }
            return output
        return ApiProcessingFailure(
            errors=["Did not found a user."],
            status=500
        )

    def validate(self, request_data: Dict[str, Any], account_member: Optional[ApiAccountMember],
                 resource: NullResource = NullResource()) -> Union[ApiValidationErrorSummary, Dict[str, Any]]:
        return {}


class MeApiView(NoResourceApiView):
    def _get_action_configuration(self) -> Dict[HttpMethod, NoResourceAction]:
        return {
            HttpMethod.GET: GetMyProfileAction()
        }

    def _get_endpoint_name(self) -> str:
        return "mobile-me"
