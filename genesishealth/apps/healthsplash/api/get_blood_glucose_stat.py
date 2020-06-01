from datetime import timedelta
from typing import Optional, Any, Dict, Union

from django.contrib.auth.models import User
from django.utils.timezone import now
from pronym_api.models import ApiAccountMember
from pronym_api.views.actions import ApiProcessingFailure, ResourceAction, ResourceT
from pronym_api.views.api_view import ResourceApiView, HttpMethod
from pronym_api.views.validation import ApiValidationErrorSummary

from genesishealth.apps.accounts.models import PatientProfile
from genesishealth.apps.gdrives.models import GDrive


class GetBloodGlucoseStatAction(ResourceAction[User]):
    def execute(
            self,
            request: Dict[str, Any],
            account_member: Optional[ApiAccountMember],
            resource: User
    ) -> Optional[Union[ApiProcessingFailure, Dict[str, Any]]]:
        user = resource
        profile: PatientProfile = user.patient_profile
        device: Optional[GDrive] = profile.get_device()
        output = {
           'id': resource.id,
           'meid': device.meid if device else None,
        }
        for i in (7, 14, 28, 90):
            average = profile.get_average_glucose_level(i)
            cutoff = now() - timedelta(days=i)
            readings = user.glucose_readings.filter(reading_datetime_utc__gt=cutoff).order_by('glucose_value')
            if len(readings) == 0:
                max_reading = None
                min_reading = None
            else:
                min_reading = readings[0].glucose_value
                max_reading = readings.order_by('-glucose_value')[0].glucose_value
            output[f'glucose_{i}_days'] = {
                'average': average,
                'max': max_reading,
                'min': min_reading,
                'line_graph': ''
            }
        cutoff = now() - timedelta(days=90)
        readings_90 = user.glucose_readings.filter(reading_datetime_utc__gt=cutoff).order_by('reading_datetime_utc')
        output['readings'] = [
            {
                'id': reading.id,
                'datetime': str(reading.reading_datetime_utc),
                'meid': device.meid if reading.device else None,
                'glucose_value': reading.glucose_value,
                'survey_response': []
            }
            for reading in readings_90
        ]
        return output

    def validate(
            self,
            request_data: Dict[str, Any],
            account_member: Optional[ApiAccountMember],
            resource: User
    ) -> Union[ApiValidationErrorSummary, Dict[str, Any]]:
        return {}


class GetBloodGlucoseStatApiView(ResourceApiView[User]):
    def _get_resource(self) -> Optional[User]:
        try:
            return User.objects.get(
                first_name=self.request.GET['first_name'],
                last_name=self.request.GET['last_name'],
                patient_profile__gender=self.request.GET['gender'],
                patient_profile__date_of_birth=self.request.GET['date_of_birth'],
                patient_profile__contact__address1=self.request.GET['address'],
                patient_profile__contact__city=self.request.GET['city'],
                patient_profile__contact__state=self.request.GET['state'],
                patient_profile__contact__zip=self.request.GET['zip_code']
            )
        except User.DoesNotExist:
            return None

    def _get_endpoint_name(self) -> str:
        return "get-blood-glucose-stat"

    def _get_action_configuration(self) -> Dict[HttpMethod, ResourceAction]:
        return {
            HttpMethod.GET: GetBloodGlucoseStatAction()
        }
