from django.db import models
from django.contrib.auth.models import User

from genesishealth.apps.utils.fields import SeparatedValuesField


class UserOptionException(Exception):
    pass


class UserOption(models.Model):
    USER_TYPE_ADMIN = 'admin'
    USER_TYPE_PROFESSIONAL = 'professional'
    USER_TYPE_PATIENT = 'patient'
    USER_TYPE_CHOICES = (
        (USER_TYPE_ADMIN, 'Admin'),
        (USER_TYPE_PROFESSIONAL, 'Professional'),
        (USER_TYPE_PATIENT, 'Patient')
    )
    name = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255, unique=True)
    default = models.CharField(max_length=255)
    options = SeparatedValuesField(null=True)
    available_to_types = SeparatedValuesField(default=[], sub_choices=USER_TYPE_CHOICES)

    class Meta:
        app_label = 'accounts'

    @classmethod
    def get_option(cls, user, option):
        if isinstance(option, str):
            try:
                option = UserOption.objects.get(name=option)
            except UserOption.DoesNotExist:
                raise Exception("get_option provided with an invalid option: %s" % option)

        try:
            oe = UserOptionEntry.objects.get(option=option, user=user)
        except UserOptionEntry.DoesNotExist:
            return option.default
        else:
            return oe.value

    @classmethod
    def get_options_by_user_type(cls, user_type):
        assert user_type in (map(lambda x: x[0], cls.USER_TYPE_CHOICES))
        return UserOption.objects.filter(available_to_types__regex='(^|,)%s(,|$)' % user_type)

    @classmethod
    def update_option(cls, user, option, new_value):
        if isinstance(option, str):
            try:
                option = UserOption.objects.get(name=option)
            except UserOption.DoesNotExist:
                raise Exception("update_option provided with an invalid option: %s" % option)
        try:
            oe = UserOptionEntry.objects.get(option=option, user=user)
        except UserOptionEntry.DoesNotExist:
            oe = UserOptionEntry(option=option, user=user)
        if not option.validate_new_value(new_value):
            raise UserOptionException('%s is not a valid option for %s' % (new_value, option))
        oe.value = new_value
        oe.save()

    def __str__(self) -> str:
        return self.display_name

    def validate_new_value(self, new_value):
        return not self.options or new_value in self.options


class UserOptionEntry(models.Model):
    option = models.ForeignKey(UserOption, related_name='entries', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='option_entries', on_delete=models.CASCADE)
    value = models.CharField(max_length=255)

    class Meta:
        app_label = 'accounts'
        unique_together = ('option', 'user')
