from typing import Optional, Dict, Any, Union, Type

from django import forms
from django.db.models import QuerySet

from pronym_api.models import ApiAccountMember
from pronym_api.views.actions import ResourceAction, ApiProcessingFailure, FormValidatedResourceAction
from pronym_api.views.api_view import HttpMethod
from pronym_api.views.model_view.views import ModelDetailApiView

from genesishealth.apps.mobile.models import MobileNotification, MobileProfile, MobileNotificationQuestionEntry


class AnswerQuestionForm(forms.Form):
    answer = forms.ModelChoiceField(queryset=None)

    def __init__(self, *args, **kwargs) -> None:
        self.question = kwargs.pop('question')
        super(AnswerQuestionForm, self).__init__(*args, **kwargs)
        self.fields['answer'].queryset = self.question.possible_answers.all()


class AnswerQuestionResourceAction(FormValidatedResourceAction[AnswerQuestionForm, MobileNotificationQuestionEntry]):
    def _get_form_class(
            self,
            request_data: Dict[str, Any],
            account_member: Optional[ApiAccountMember],
            resource: MobileNotificationQuestionEntry
    ) -> Type[AnswerQuestionForm]:
        return AnswerQuestionForm

    def _get_form_kwargs(self, request_data: Dict[str, Any], account_member: Optional[ApiAccountMember],
                         resource: MobileNotificationQuestionEntry) -> Dict[str, Any]:
        return {
            'question': resource.question
        }

    def execute(
        self,
        request: Dict[str, Any],
        account_member: Optional[ApiAccountMember],
        resource: MobileNotificationQuestionEntry
    ) -> Optional[Union[ApiProcessingFailure, Dict[str, Any]]]:
        form = self._get_form(request, account_member, resource)
        resource.answer = form.cleaned_data['answer']
        resource.save()
        return {}


class AnswerQuestionMobileNotificationApiView(ModelDetailApiView[MobileNotificationQuestionEntry]):
    def _get_action_configuration(self) -> Dict[HttpMethod, ResourceAction]:
        return {
            HttpMethod.POST: AnswerQuestionResourceAction()
        }

    def _check_authorization(
            self,
            requester: ApiAccountMember,
            resource: Optional[MobileNotificationQuestionEntry],
            action: ResourceAction
    ) -> bool:
        try:
            self.authenticated_account_member.user.mobile_profile
        except MobileProfile.DoesNotExist:
            return False
        return True

    def _get_model(self) -> Type[MobileNotificationQuestionEntry]:
        return MobileNotificationQuestionEntry

    def _get_queryset(self) -> 'QuerySet[MobileNotificationQuestionEntry]':
        return MobileNotificationQuestionEntry.objects.filter(
            notification__profile=self.authenticated_account_member.user.mobile_profile
        )
