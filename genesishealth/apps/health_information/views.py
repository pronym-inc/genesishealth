from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User

from genesishealth.apps.health_information.models import (
    HealthInformation, HealthProfessionalTargets)
from genesishealth.apps.health_information.forms import (
    HealthInformationForm, HealthProfessionalTargetsForm)
from genesishealth.apps.utils.request import (
    professional_or_patient_user, professional_user, debug_response)
from genesishealth.apps.utils.views import generic_form


@login_required
@user_passes_test(professional_or_patient_user)
def edit(request, patient_id=None, group_id=None):
    try:
        if patient_id:
            assert request.user.is_professional()
            patient = request.user.professional_profile.get_patients().get(
                pk=patient_id)
        else:
            assert request.user.is_patient()
            patient = request.user
    except (User.DoesNotExist, AssertionError) as e:
        return debug_response(e)

    try:
        hi = HealthInformation.objects.get(patient=patient)
    except HealthInformation.DoesNotExist:
        hi = HealthInformation(patient=patient)
    message = '%s health information has been updated.' % (
        request.user.is_patient() and 'Your' or 'The patient\'s')
    return generic_form(
        request,
        form_class=HealthInformationForm,
        page_title='Edit Health Targets',
        system_message=message,
        go_back_until=[
            'edit-health-information-for-patient', 'edit-health-information'],
        form_kwargs={'instance': hi})


@user_passes_test(professional_user)
def edit_targets(request, patient_id):
    try:
        patient = request.user.professional_profile.get_patients().get(
            pk=patient_id)
        targets = HealthProfessionalTargets.objects.get_or_create(
            patient=patient, professional=request.user)
    except (User.DoesNotExist, HealthProfessionalTargets.DoesNotExist) as e:
        return debug_response(e)

    return generic_form(
        request,
        form_class=HealthProfessionalTargetsForm,
        page_title='Edit Health Targets for %s' % patient.get_reversed_name(),
        system_message='The patient\'s targets have been updated.',
        form_kwargs={'instance': targets})
