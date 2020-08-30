from typing import Dict, Any, Optional, Type

from django.forms import ModelForm
from pronym_api.models import ApiAccountMember
from pronym_api.views.actions import NoResourceFormAction, ResourceAction, NullResource
from pronym_api.views.api_view import NoResourceApiView, HttpMethod

from genesishealth.apps.mobile.models import MobileProfile


class UpdateExpoPushTokenForm(ModelForm):
    class Meta:
        model = MobileProfile
        fields = ('expo_push_token',)


class UpdateExpoPushTokenAction(NoResourceFormAction[UpdateExpoPushTokenForm]):
    def _get_form_class(self, request_data: Dict[str, Any], account_member: Optional[ApiAccountMember],
                        resource: NullResource) -> Type[UpdateExpoPushTokenForm]:
        return UpdateExpoPushTokenForm

    def _get_form_kwargs(self, request_data: Dict[str, Any], account_member: Optional[ApiAccountMember],
                         resource: NullResource) -> Dict[str, Any]:
        if account_member is not None:
            return {
                'instance': account_member.user.mobile_profile
            }
        return {}


class UpdateExpoPushTokenApiView(NoResourceApiView):

    def _check_authorization(self, requester: ApiAccountMember, resource: Optional[NullResource], action: ResourceAction) -> bool:
        try:
            requester.user.mobile_profile
        except MobileProfile.DoesNotExist:
            return False
        return True

    def _get_action_configuration(self) -> Dict[HttpMethod, ResourceAction]:
        return {
            HttpMethod.POST: UpdateExpoPushTokenAction()
        }

    def _get_endpoint_name(self) -> str:
        return "update-expo-push-token"
