from datetime import timedelta

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.utils.timezone import now

from genesishealth.apps.utils.class_views import (
    GenesisBaseDetailPane, GenesisDetailView)
from genesishealth.apps.utils.request import admin_user


test = user_passes_test(admin_user)


class InformationPane(GenesisBaseDetailPane):
    template_name = "ghtadmin/dashboard/panes/information.html"
    pane_title = "Information"


class PasswordPane(GenesisBaseDetailPane):
    template_name = "ghtadmin/dashboard/panes/password.html"
    pane_title = "Password History"


class RolesPane(GenesisBaseDetailPane):
    template_name = "ghtadmin/dashboard/panes/roles.html"
    pane_title = "Roles"


class AdminDashboardView(GenesisDetailView):
    pane_classes = (InformationPane, RolesPane, PasswordPane)
    page_title = "Admin Dashboard"

    def get_pane_context(self):
        logins = self.request.user.login_records.order_by('-datetime')
        if logins.count() > 0:
            last_login_dt = logins[0].datetime
        else:
            last_login_dt = None
        login_count = logins.filter(
            datetime__gt=now() - timedelta(days=30)).count()
        prev_passwords = self.request.user.previous_passwords.order_by(
            '-date_added')
        if prev_passwords.count() == 0:
            password_last_changed = self.request.user.date_joined
        else:
            pw = prev_passwords[0]
            password_last_changed = pw.date_added
        next_password_change = password_last_changed + timedelta(
            days=settings.PASSWORD_CHANGE_INTERVAL)
        admin_profile = self.request.user.admin_profile
        group_str = ", ".join(map(
            lambda x: x.name, admin_profile.permission_groups.all()))
        permission_str = ", ".join(map(
            lambda x: x.name, admin_profile.get_all_permissions()))
        return {
            'user': self.request.user,
            'login_count': login_count,
            'password_last_changed': password_last_changed,
            'next_password_change': next_password_change,
            'last_login_dt': last_login_dt,
            'permission_groups': group_str,
            'permissions': permission_str
        }
main = test(AdminDashboardView.as_view())
