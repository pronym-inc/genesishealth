from datetime import timedelta
from json import loads, dumps

from django.conf import settings
from django.urls import resolve, reverse, Resolver404
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now

from genesishealth.apps.utils.func import utcnow


class SessionHistory(object):
    """Tracks what screens user has gone to, then used for sending
    them backwards."""
    MAX_SIZE = 10
    SESSION_KEY = 'genesis_history'
    HEADER_NAME = 'HTTP_DASHBOARDREQ'

    @classmethod
    def load(cls, request):
        data = request.session.get(cls.SESSION_KEY)
        if data is not None:
            return cls(loads(data))
        return cls()

    def __init__(self, history=None):
        if history is None:
            history = []
        self.history = history

    def __str__(self) -> str:
        return repr(self.history)

    def add_request(self, request):
        try:
            view_name = resolve(request.path).view_name
        except Resolver404:
            pass
        else:
            self.push(request.path, view_name)
        self.save(request)

    def push(self, path, view_name):
        entry = (path, view_name)
        if len(self.history) > 0 and self.history[-1] == entry:
            return
        if len(self.history) >= self.MAX_SIZE:
            first_index = len(self.history) - self.MAX_SIZE + 1
            self.history = self.history[first_index:]
        self.history.append(entry)

    def pop(self, up_to=1, stop_if_in=None):
        if stop_if_in is None:
            stop_if_in = []
        entry = None
        first = len(self.history) > 0 and self.history[-1] or None
        for i in range(min(up_to + 1, len(self.history))):
            entry = self.history.pop()
            if entry[1] in stop_if_in or len(self.history) == 0:
                break

        if entry and stop_if_in and not entry[1] in stop_if_in:
            entry = first

        return entry

    def save(self, request, commit=True):
        request.session[self.SESSION_KEY] = dumps(self.history)


class StoreSessionHistoryMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if (response.status_code == 200 and
                request.META.get(SessionHistory.HEADER_NAME)):
            history = SessionHistory.load(request)
            history.add_request(request)
        return response


class LastTouchedMiddleware(MiddlewareMixin):
    def process_request(self, request):
        try:
            profile = request.user.get_profile()
        except (Exception, AttributeError):
            pass
        else:
            profile.last_touched = utcnow()
            profile.save()


def should_check_password(user):
    if user.is_patient():
        group = user.patient_profile.group
    elif user.is_professional():
        group = user.professional_profile.parent_group
    else:
        group = None
    if group is not None and group.is_demo_group:
        return False
    try:
        prev_pass = user.previous_passwords.all()[0]
    except IndexError:
        return False
    return prev_pass.date_added < now() - timedelta(
        days=settings.PASSWORD_CHANGE_INTERVAL)


class SecurityRedirectMiddleware(MiddlewareMixin):
    def process_request(self, request):
        try:
            profile = request.user.get_profile()
        except (Exception, AttributeError):
            if not request.user.is_staff:
                return
            requested_with = request.META.get('HTTP_X_REQUESTED_WITH')
            if should_check_password(request.user):
                if requested_with == "XMLHttpRequest":
                    allowed_paths = (
                        reverse('accounts:update-password-expired'),
                        reverse('accounts:logout'),)
                    if request.path not in allowed_paths:
                        return HttpResponse(
                            dumps({
                                "redirect": reverse(
                                    'accounts:update-password-expired')}))
        else:
            pass_expired = should_check_password(request.user)
            if (not profile.configured or
                    profile.is_reset_password or
                    not profile.is_accepted_terms or
                    not profile.is_accepted_privacy or
                    pass_expired):
                if not profile.is_accepted_terms:
                    view_name = 'accounts:accept-terms'
                elif not profile.is_accepted_privacy:
                    view_name = 'accounts:accept-privacy'
                elif not profile.configured:
                    view_name = 'accounts:setup-security'
                elif profile.is_reset_password:
                    view_name = 'accounts:reset-password-finish'
                elif pass_expired:
                    view_name = 'accounts:update-password-expired'
                else:
                    raise Exception
                security_path = reverse(view_name)
                requested_with = request.META.get('HTTP_X_REQUESTED_WITH')
                if requested_with == "XMLHttpRequest":
                    allowed_paths = (
                        reverse('accounts:setup-security'),
                        reverse('accounts:reset-password-finish'),
                        reverse('accounts:accept-terms'),
                        reverse('accounts:accept-privacy'),
                        reverse('accounts:logout'),
                        reverse('contact:contact-main'),
                        reverse('accounts:update-password-expired'),
                        '/terms/',
                        '/privacy/',
                        '/404/',
                        '/500/',
                    )
                    if request.path not in allowed_paths:
                        return HttpResponse(
                            dumps({"redirect": security_path}))
                else:
                    dashboard_path = reverse('dashboard:index')
                    if request.path != dashboard_path:
                        return HttpResponseRedirect(
                            ''.join([settings.DASHBOARD_PREFIX,
                                     security_path]))
