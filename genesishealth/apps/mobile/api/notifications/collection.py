from typing import Optional, Dict, Type

from django.db.models.query import QuerySet
from pronym_api.models import ApiAccountMember
from pronym_api.views.actions import ResourceAction
from pronym_api.views.api_view import HttpMethod
from pronym_api.views.model_view.views import ModelCollectionApiView

from genesishealth.apps.mobile.models import MobileProfile
from genesishealth.apps.mobile.models.mobile_notification import MobileNotification


class MobileNotificationCollectionApiView(ModelCollectionApiView[MobileNotification]):
    def _get_action_configuration(self) -> Dict[HttpMethod, ResourceAction]:
        config = super(MobileNotificationCollectionApiView, self)._get_action_configuration()
        del config[HttpMethod.POST]
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
