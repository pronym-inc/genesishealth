from genesishealth.apps.contact.forms import ContactForm
from genesishealth.apps.utils.views import generic_form


def contact(request):
    """Contact form view"""
    return generic_form(request, 
                form_class=ContactForm,
                form_kwargs={'requester': request.user},
                page_title='Contact Us', 
                go_back_until=(('contact:contact-main',),),
                system_message='Your message has been sent.  We appreciate your feedback.')
