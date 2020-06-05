from datetime import timedelta
from typing import Optional, Any, Dict, Union

from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.utils.timezone import now
from pronym_api.models import ApiAccountMember
from pronym_api.views.actions import ApiProcessingFailure, ResourceAction, ResourceT
from pronym_api.views.api_view import ResourceApiView, HttpMethod
from pronym_api.views.validation import ApiValidationErrorSummary

from genesishealth.apps.accounts.models import PatientProfile
from genesishealth.apps.gdrives.models import GDrive
from genesishealth.apps.readings.models import GlucoseReading


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
            'demographic_data': {
               'first_name': user.first_name,
               'last_name': user.last_name,
               'gender': profile.gender,
               'date_of_birth': str(profile.date_of_birth),
               'address': profile.contact.address1,
               'city': profile.contact.city,
               'state': profile.contact.state,
               'zip_code': profile.contact.zip
            },
            'product_type': 'Glucose Monitor',
            'product_name': 'GHT Glucose Meter'
        }
        for i in (7, 14, 28, 90):
            output[f'glucose_{i}_days'] = self.__get_reading_data_for_period(user, i)
        cutoff = now() - timedelta(days=90)
        readings_90: 'QuerySet[GlucoseReading]' = user.glucose_readings.filter(
            reading_datetime_utc__gt=cutoff).order_by('reading_datetime_utc')
        reading: GlucoseReading
        output['readings'] = [
            {
                'id': reading.id,
                'datetime': str(reading.reading_datetime_utc),
                'meid': device.meid if reading.device else None,
                'glucose_value': reading.glucose_value,
                'survey_response': [
                    {
                        'question': 'Was this reading pre-meal, post-meal, or normal?',
                        'answer': reading.get_measure_type_display()
                    }
                ]
            }
            for reading in readings_90
        ]
        return output

    @staticmethod
    def __get_reading_data_for_period(user: User, days: int) -> Dict[str, Any]:
        average = user.patient_profile.get_average_glucose_level(days)
        cutoff = now() - timedelta(days=days)
        readings = user.glucose_readings.filter(reading_datetime_utc__gt=cutoff).order_by('glucose_value')
        if len(readings) == 0:
            max_reading = None
            min_reading = None
        else:
            min_reading = readings[0].glucose_value
            max_reading = readings.order_by('-glucose_value')[0].glucose_value
        return {
            'average': average,
            'max': max_reading,
            'min': min_reading,
            'line_graph': ''
        }

    def validate(
            self,
            request_data: Dict[str, Any],
            account_member: Optional[ApiAccountMember],
            resource: User
    ) -> Union[ApiValidationErrorSummary, Dict[str, Any]]:
        return {}


class GetBloodGlucoseStatApiView(ResourceApiView[User]):
    def _get_resource(self) -> Optional[User]:
        # If their request contains an id parameter, we'll try to look up using that, otherwise we'll look
        # at their GET parameters.
        qs = User.objects.filter(patient_profile__isnull=False)
        if 'id' in self.request.GET:
            try:
                return qs.get(pk=self.request.GET['id'])
            except User.DoesNotExist:
                return None
        required_fields = ('first_name', 'last_name', 'gender', 'date_of_birth', 'address', 'city', 'state', 'zip_code')
        has_required_fields = True
        for field in required_fields:
            if field not in self.request.GET:
                has_required_fields = False
                break
        if has_required_fields:
            try:
                return qs.get(
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
                pass
        return None

    def _get_endpoint_name(self) -> str:
        return "get-blood-glucose-stat"

    def _get_action_configuration(self) -> Dict[HttpMethod, ResourceAction]:
        return {
            HttpMethod.GET: GetBloodGlucoseStatAction()
        }
