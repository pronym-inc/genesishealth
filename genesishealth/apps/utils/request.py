import json

from django.http import HttpResponse
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.models import AnonymousUser

from genesishealth.apps.utils.func import system_message
from genesishealth.apps.utils.middleware import SessionHistory


def json_response(content):
    return HttpResponse(json.dumps(content), content_type="application/json")


def genesis_redirect(
        request, url, steps_back=1, go_back_until=None,
        max_steps_back=5, then_download_id=None, raw_redirect=False,
        *args, **kwargs):
    """Our AJAX interface is bad with redirects, so in order to keep
    url accurate, we need to actually send redirects as JSON objects that
    are handled by client."""
    if go_back_until is None:
        go_back_until = []
    if not url:
        history = SessionHistory.load(request)
        try:
            if go_back_until:
                url = history.pop(max_steps_back, go_back_until)[0]
            else:
                url = history.pop(steps_back)[0]
        except (AttributeError, TypeError):
            url = ''
        history.save(request)
    raw_data = {'redirect': url, 'raw_redirect': raw_redirect}
    if then_download_id is not None:
        raw_data['then_download'] = reverse(
            'reports:temp-download', args=[then_download_id])
    data = json.dumps(raw_data)
    if request.POST.get('X-Requested-With') == 'IFrame':
        data = '<textarea data-type="application/json">{0}</textarea>'.format(
            data)
    return HttpResponse(data)


def redirect_with_message(
        request, redirect_to, message, go_back_until=None, *args, **kwargs):
    """Sends a redirect with a system message."""
    if go_back_until is None:
        go_back_until = []
    system_message(request, message)
    return genesis_redirect(
        request, redirect_to, go_back_until=go_back_until, *args, **kwargs)


def debug_response(exception):
    if settings.DEBUG:
        return HttpResponse(repr(exception))
    return HttpResponse(status=500)


def check_user_type(user, types):
    if isinstance(user, AnonymousUser):
        return False
    for type_ in types:
        try:
            type_, _ = type_.split('/')
        except ValueError:
            pass
        if type_ == 'Admin':
            if user.is_admin():
                return True
        elif type_ == 'Professional':
            if user.is_professional():
                return True
        elif type_ == 'Patient':
            if user.is_patient():
                return True
    return False


def admin_user(user):
    return user.is_authenticated and user.is_admin()


def professional_user(user):
    return user.is_authenticated and user.is_professional()


def patient_user(user):
    return user.is_authenticated and user.is_patient()


def professional_or_patient_user(user):
    return professional_user(user) or patient_user(user)


def require_admin_permission(permission_name):
    def new_func(func):
        def newer_func(request, *args, **kwargs):
            if not request.user.is_admin():
                return debug_response("Admin required!")
            if not request.user.admin_profile.has_permission(permission_name):
                return debug_response("Permission {0} required!".format(
                    permission_name))
            return func(request, *args, **kwargs)
        return newer_func
    return new_func


def superuser_user(user):
    return user.is_authenticated and user.is_superuser
