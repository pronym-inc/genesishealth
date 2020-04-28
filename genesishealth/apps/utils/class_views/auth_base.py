from django.http import HttpResponseNotFound
from django.views.generic import View, TemplateView


class AuthViewMixin(object):
    authorized_user_types = []

    def check_authorized_user(self):
        # Let them through if they didn't provided any authorized
        # types
        authorized_types = self.get_authorized_user_types()
        if len(authorized_types) == 0:
            return True
        user_type = self.request.user.get_user_type()
        return user_type in authorized_types

    def get_authorized_user_types(self):
        return self.authorized_user_types


class AuthView(View, AuthViewMixin):
    def dispatch(self, request, *args, **kwargs):
        if not self.check_authorized_user():
            return HttpResponseNotFound()
        return super(AuthView, self).dispatch(request, *args, **kwargs)


class AuthTemplateView(TemplateView, AuthViewMixin):
    def dispatch(self, request, *args, **kwargs):
        if not self.check_authorized_user():
            return HttpResponseNotFound()
        return super(AuthTemplateView, self).dispatch(request, *args, **kwargs)
