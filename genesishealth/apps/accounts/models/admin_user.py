from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from django.contrib.auth.models import User


class AdminProfile(models.Model):
    user: 'User' = models.OneToOneField(
        'auth.User', related_name='admin_profile',
        limit_choices_to={
            'patient_profile__isnull': True,
            'professional_profile__isnull': True},
        on_delete=models.CASCADE)
    is_super_user: bool = models.BooleanField(default=False)
    permissions = models.ManyToManyField(
        'AdminPermission',
        related_name='admin_users',
        blank=True)
    permission_groups = models.ManyToManyField(
        'AdminPermissionGroup', related_name='members',
        blank=True)

    def __str__(self) -> str:
        return "{0}'s admin profile".format(self.user)

    def get_all_permissions(self):
        if self.is_super_user:
            return AdminPermission.objects.all()
        permission_ids = set([p.id for p in self.permissions.all()])
        for group in self.permission_groups.all():
            for permission in group.permissions.all():
                permission_ids.add(permission.id)
        return AdminPermission.objects.filter(id__in=permission_ids)

    def handle_login(self) -> None:
        from genesishealth.apps.accounts.models.profile_base import LoginRecord
        LoginRecord(user=self.user).save()

    def has_permission(self, permission_name):
        if self.is_super_user:
            return True
        try:
            self.get_all_permissions().get(name=permission_name)
        except AdminPermission.DoesNotExist:
            return False
        return True

    @property
    def all_permissions(self):
        if not hasattr(self, '_permission_names'):
            self._permission_names = list(map(
                lambda x: x.name, self.get_all_permissions()))
        return self._permission_names


class AdminPermission(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self) -> str:
        return "Permission: {0}".format(self.name)


class AdminPermissionGroup(models.Model):
    name = models.CharField(max_length=255, unique=True)
    permissions = models.ManyToManyField(
        'AdminPermission', related_name='groups')

    def __str__(self) -> str:
        return "Group: {0}".format(self.name)
