from typing import Dict

from pronym_api.api.get_token import GetTokenApiView, CreateTokenResourceAction
from pronym_api.views.actions import BaseAction
from pronym_api.views.api_view import HttpMethod


class GenesisGetTokenApiView(GetTokenApiView):
    def _get_action_configuration(self) -> Dict[HttpMethod, BaseAction]:
        config: Dict[HttpMethod, BaseAction] = super()._get_action_configuration()
        config.update({
            HttpMethod.GET: CreateTokenResourceAction()
        })
        return config
