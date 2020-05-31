from django.db import models
from django.contrib.auth.models import User


class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', null=True, on_delete=models.CASCADE)
    recipients = models.ManyToManyField(User, related_name='received_messages')
    subject = models.CharField(max_length=255)
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'accounts'

    def recipient_list(self) -> str:
        return ', '.join(map(lambda x: "%s, %s (%s)" % x, self.recipients.all().values_list('last_name', 'first_name', 'email')))

    def send(self) -> None:
        for r in self.recipients.all():
            try:
                MessageEntry.objects.get(recipient=r, message=self)
            except MessageEntry.DoesNotExist:
                new_entry = MessageEntry(recipient=r, message=self)
                new_entry.save()


class MessageEntry(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.ForeignKey(Message, related_name='message_entries', on_delete=models.CASCADE)
    read = models.BooleanField(default=False)

    class Meta:
        app_label = 'accounts'
        unique_together = ('recipient', 'message')
        verbose_name = 'message entry'
        verbose_name_plural = 'message entries'

    def __str__(self) -> str:
        return 'Message %s from %s (%s)' % (self.message.subject, self.message.sender, self.message.sent_at)
