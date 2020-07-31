from django.db import models


class WorkQueueProfile(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='work_queue_profile')
    allowed_types = models.ManyToManyField('WorkQueueType', related_name='+')

    def __str__(self) -> str:
        return str(self.user)
