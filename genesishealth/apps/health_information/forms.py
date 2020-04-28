from django.forms import ModelForm, ValidationError

from genesishealth.apps.health_information.models import HealthInformation, HealthProfessionalTargets
from genesishealth.apps.utils.forms import GenesisModelForm


class HealthInformationForm(ModelForm):
    class Meta:
        model = HealthInformation
        fields = (
            'premeal_glucose_goal_minimum', 'premeal_glucose_goal_maximum', 'postmeal_glucose_goal_minimum',
            'postmeal_glucose_goal_maximum', 'safe_zone_minimum', 'safe_zone_maximum', 'compliance_goal',
            'minimum_compliance')

    def ensure_max(self, min_key, max_key):
        min_ = self.cleaned_data.get(min_key)
        max_ = self.cleaned_data.get(max_key)

        try:
            if int(min_) >= int(max_):
                raise ValidationError("Maximum glucose goal must be greater than minimum goal.")
        except TypeError:
            raise ValidationError("All entries must be provided as numbers.")

    def clean_premeal_glucose_goal_maximum(self):
        self.ensure_max('premeal_glucose_goal_minimum', 'premeal_glucose_goal_maximum')
        return self.cleaned_data.get('premeal_glucose_goal_maximum')

    def clean_postmeal_glucose_goal_maximum(self):
        self.ensure_max('postmeal_glucose_goal_minimum', 'postmeal_glucose_goal_maximum')
        return self.cleaned_data.get('postmeal_glucose_goal_maximum')

    def clean_safe_zone_maximum(self):
        self.ensure_max('safe_zone_minimum', 'safe_zone_maximum')
        return self.cleaned_data.get('safe_zone_maximum')


class HealthProfessionalTargetsForm(GenesisModelForm):
    class Meta:
        model = HealthProfessionalTargets
        exclude = ('patient', 'professional')
