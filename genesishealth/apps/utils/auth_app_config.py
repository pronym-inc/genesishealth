from django.contrib.auth.apps import AuthConfig


class AuthAppConfig(AuthConfig):
    def ready(self):
        super(AuthAppConfig, self).ready()

        User = self.get_model('User')  # noqa

        def get_profile(self):
            for clsName in (
                    'patient_profile',
                    'professional_profile',
                    'demo_profile'):
                try:
                    profile = getattr(self, clsName)
                except:
                    pass
                else:
                    return profile

            raise Exception("Profile not found for user: %s" % self)

        def has_group(self, group):
            try:
                self.groups.get(name=group)
            except:
                return False
            return True

        def is_admin(self):
            try:
                self.admin_profile
            except:
                return False
            return True

        def is_professional(self):
            try:
                assert not self.is_admin()
                self.professional_profile
            except:
                return False
            return True

        def is_patient(self):
            try:
                assert not self.is_admin()
                self.patient_profile
            except:
                return False
            return True

        def get_user_type(self):
            for name in ('patient', 'professional', 'admin'):
                if hasattr(self, 'is_%s' % name):
                    fn = getattr(self, 'is_%s' % name)
                    if fn():
                        return name
            return 'unknown'

        def get_initials(self):
            if self.last_name and self.first_name:
                return self.first_name[0] + self.last_name[0]
            return self.username

        def get_reversed_name(self):
            if self.last_name and self.first_name:
                return "%s, %s" % (
                    self.last_name, self.first_name)
            return self.username

        User.get_profile = get_profile
        User.has_group = has_group
        User.is_admin = is_admin
        User.is_professional = is_professional
        User.is_patient = is_patient
        User.get_initials = get_initials
        User.get_user_type = get_user_type
        User.get_reversed_name = get_reversed_name
