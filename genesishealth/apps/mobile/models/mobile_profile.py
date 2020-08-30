from django.db import models


class MobileProfile(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='mobile_profile')
    expo_push_token = models.TextField()

    def __str__(self) -> str:
        return str(self.user)
