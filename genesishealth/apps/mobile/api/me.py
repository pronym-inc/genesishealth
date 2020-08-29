from typing import Dict, Any, Optional, Union

from pronym_api.models import ApiAccountMember
from pronym_api.views.actions import NoResourceAction, NullResource, ApiProcessingFailure
from pronym_api.views.api_view import HttpMethod, NoResourceApiView
from pronym_api.views.validation import ApiValidationErrorSummary


class GetMyProfileAction(NoResourceAction):
    def execute(self, request: Dict[str, Any], account_member: Optional[ApiAccountMember],
                resource: NullResource = NullResource()) -> Optional[Union[ApiProcessingFailure, Dict[str, Any]]]:
        if account_member is not None:
            return {
                "first_name": account_member.user.first_name,
                "last_name": account_member.user.last_name
            }
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
        pass