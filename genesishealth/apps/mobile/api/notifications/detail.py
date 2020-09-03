from typing import Type, Optional, Dict, Any, Union

from django.db.models import QuerySet

from pronym_api.models import ApiAccountMember
from pronym_api.views.actions import ResourceAction, ApiProcessingFailure
from pronym_api.views.api_view import HttpMethod
from pronym_api.views.model_view.actions.retrieve import RetrieveModelResourceAction
from pronym_api.views.model_view.views import ModelDetailApiView

from genesishealth.apps.mobile.models import MobileNotification, MobileProfile, MobileNotificationQuestionEntry


class MobileNotificationRetrieveModelResourceAction(RetrieveModelResourceAction[MobileNotification]):
    def execute(
            self,
            request: Dict[str, Any],
            account_member: Optional[ApiAccountMember],
            resource: MobileNotification
    ) -> Optional[Union[ApiProcessingFailure, Dict[str, Any]]]:
        output = super().execute(request, account_member, resource)
        if isinstance(output, dict):
            question_entry: MobileNotificationQuestionEntry
            output['questions'] = [
                {
                    'id': question_entry.id,
                    'question_text': question_entry.question.text,
                    'possible_answers': [
                        {
                            'id': answer.id,
                            'text': answer.text
                        }
                        for answer in question_entry.question.possible_answers.all()
                    ],
                    'selected_answer': question_entry.answer.id if question_entry.answer is not None else None
                } for question_entry in resource.question_entries.all()
            ]
        return output


class MobileNotificationDetailApiView(ModelDetailApiView[MobileNotification]):
    def _get_action_configuration(self) -> Dict[HttpMethod, ResourceAction]:
        config = super()._get_action_configuration()
        del config[HttpMethod.PUT]
        config[HttpMethod.GET] = MobileNotificationRetrieveModelResourceAction()
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
