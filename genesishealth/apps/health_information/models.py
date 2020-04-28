from django.db import models
from django.contrib.auth.models import User


class HealthTargetBase(models.Model):
    """Manages health targets for a user."""
    class Meta:
        abstract = True

    premeal_glucose_goal_minimum = models.IntegerField(default=70)
    premeal_glucose_goal_maximum = models.IntegerField(default=130)
    postmeal_glucose_goal_minimum = models.IntegerField(default=90)
    postmeal_glucose_goal_maximum = models.IntegerField(default=180)
    safe_zone_minimum = models.IntegerField(default=60)
    safe_zone_maximum = models.IntegerField(default=250)
    compliance_goal = models.IntegerField(
        default=3, help_text="Number of required daily tests")
    minimum_compliance = models.IntegerField(default=1)


class HealthProfessionalTargetsManager(models.Manager):
    def get_or_create(self, professional, patient):
        try:
            return self.model.objects.get(
                professional=professional, patient=patient)
        except self.model.DoesNotExist:
            return self.model.objects.create(
                professional=professional, patient=patient)


class HealthProfessionalTargets(HealthTargetBase):
    """A professional's custom set of targets for a patient."""
    patient = models.ForeignKey(
        User, limit_choices_to={'patient_profile__isnull': False},
        related_name='+', on_delete=models.CASCADE)
    professional = models.ForeignKey(
        User, limit_choices_to={'professional_profile__isnull': False},
        related_name='custom_health_targets', on_delete=models.CASCADE)

    objects = HealthProfessionalTargetsManager()

    class Meta:
        unique_together = ('patient', 'professional')


class HealthInformation(HealthTargetBase):
    """A user's personal health goals."""
    patient = models.OneToOneField(User, on_delete=models.CASCADE)
