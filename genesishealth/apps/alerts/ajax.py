import json

from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from genesishealth.apps.utils.request import professional_user
from genesishealth.apps.alerts.models import ProfessionalAlert, AlertTemplate


@login_required
def notifications(request):
    if request.user.is_admin():
        resp = {}
    else:
        messages = request.user.get_profile().get_unread_messages()
        resp = {'messages': [{'id': message.id, 'message_text': message.subject} for message in messages]}
        if request.user.is_professional():
            notifications = request.user.professional_profile.get_unread_alert_notifications().order_by('-sent_on')
            resp['notifications'] = [{'id': i.id, 'message_text': '%s triggered at %s' % (i.alert.name, i.sent_on)} for i in notifications]
    return HttpResponse(json.dumps(resp), content_type='application/json')


@user_passes_test(professional_user)
@require_POST
@csrf_exempt
def patient_permissions(request):
    """This should move."""
    patient_ids = map(int, request.POST.get('patients').split(','))
    patients = request.user.professional_profile.parent_group.get_patients().filter(pk__in=patient_ids)
    permissions = map(lambda x: x.strip(), request.POST.get('permissions').split(','))
    professionals = request.user.professional_profile.parent_group.professionals.none()
    c = [{'name': i.get_full_name(), 'id': i.id} for i in professionals]
    return HttpResponse(json.dumps(c), content_type='json/application')


@user_passes_test(professional_user)
def template(request, template_id):
    try:
        template = request.user.professional_profile.parent_group.alert_templates.get(pk=template_id)
    except AlertTemplate.DoesNotExist:
        return HttpResponse(status=500)

    c = {
        'recipient_type': template.recipient_type,
        'type': template.type,
        'contact_methods': [i for i in ProfessionalAlert.CONTACT_METHODS if getattr(template, i) == True],
        'message': template.message
    }

    return HttpResponse(json.dumps(c), content_type='json/application')
