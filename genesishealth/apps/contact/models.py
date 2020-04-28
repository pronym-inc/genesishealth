from django.db import models
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import send_mail


class ContactFormSubmission(models.Model):
    """Database record of someone filling out the contact form."""
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    subject = models.CharField(max_length=255)
    content = models.TextField('Message')

    def send_email(self):
        """Sends email out to admins informing them of new submission."""
        message = render_to_string('contact/email.tpl', {'submission': self})
        from_email = settings.CONTACT_FORM_FROM_EMAIL
        recipients = settings.CONTACT_FORM_EMAIL_RECIPIENTS
        send_mail(self.subject, message, from_email, recipients)
