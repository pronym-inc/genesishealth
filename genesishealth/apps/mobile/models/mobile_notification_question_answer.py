from django.db import models


class MobileNotificationQuestionAnswer(models.Model):
    question = models.ForeignKey(
        'MobileNotificationQuestion',
        on_delete=models.CASCADE,
        related_name='possible_answers'
    )
    text = models.CharField(max_length=255)
