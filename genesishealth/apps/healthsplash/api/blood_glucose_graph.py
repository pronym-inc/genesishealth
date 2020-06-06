import logging
from typing import Type, Optional, Dict, Any, List

from django.db.models import QuerySet
from django.http.response import HttpResponse, HttpResponseBase

from pronym_api.views.api_view import HttpMethod
from pronym_api.views.model_view.views import ModelDetailApiView

from genesishealth.apps.healthsplash.models.blood_glucose_graph import BloodGlucoseGraph


logger = logging.getLogger('blood_glucose_graph')


class BloodGlucoseGraphDetailApiView(ModelDetailApiView[BloodGlucoseGraph]):
    """An endpoint for retrieving a blood glucose graph."""

    def _generate_response(self, response_data: Optional[Dict[str, Any]], status_code: int) -> HttpResponseBase:
        """Override to return back the file contents instead of JSON."""
        if status_code != 200:
            return super()._generate_response(response_data, status_code)
        graph = self._get_resource()
        if graph is None:  # Should never happen!
            logger.warning("Trying to send back the image, but the resource doesn't exist!")
            return HttpResponse(status=404)
        f = graph.image.open('rb')
        return HttpResponse(f, content_type="image/png")

    def _get_allowed_methods(self) -> List[HttpMethod]:
        return [HttpMethod.GET]

    def _get_model(self) -> Type[BloodGlucoseGraph]:
        return BloodGlucoseGraph

    def _get_queryset(self) -> 'QuerySet[BloodGlucoseGraph]':
        return BloodGlucoseGraph.objects.all()

    def _get_redacted_response_payload_str(self, response: HttpResponseBase) -> str:
        return ''
