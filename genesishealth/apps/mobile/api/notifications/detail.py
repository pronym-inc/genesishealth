from typing import Type, Optional, Dict

from django.db.models import QuerySet
from pronym_api.models import ApiAccountMember
from pronym_api.views.actions import ResourceAction
from pronym_api.views.api_view import HttpMethod
from pronym_api.views.model_view.views import ModelDetailApiView

from genesishealth.apps.mobile.models import MobileNotification, MobileProfile


class MobileNotificationDetailApiView(ModelDetailApiView[MobileNotification]):
    def _get_action_configuration(self) -> Dict[HttpMethod, ResourceAction]:
        config = super()._get_action_configuration()
        del config[HttpMethod.PUT]
        return config

    def _check_authorization(
            self,
            requester: ApiAccountMember,
            resource: Optional[MobileNotification],
            action: ResourceAction
    ) -> bool:
        try:
            self.authenticated_account_member.user.mobile_profile
        except MobileProfile.DoesNotExist:
            return False
        return True

    def _get_model(self) -> Type[MobileNotification]:
        return MobileNotification

    def _get_queryset(self) -> 'QuerySet[MobileNotification]':
        return self.authenticated_account_member.user.mobile_profile.notifications.all()
