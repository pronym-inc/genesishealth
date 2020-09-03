from django.db import models


class MobileNotificationQuestionEntry(models.Model):
    notification = models.ForeignKey('MobileNotification', on_delete=models.CASCADE, related_name='question_entries')
    question = models.ForeignKey('MobileNotificationQuestion', on_delete=models.CASCADE, related_name='+')
    answer = models.ForeignKey(
        'MobileNotificationQuestionAnswer',
        on_delete=models.SET_NULL,
        null=True,
        related_name='+'
    )
    ordering = models.PositiveIntegerField()

    class Meta:
        ordering = ['ordering']
