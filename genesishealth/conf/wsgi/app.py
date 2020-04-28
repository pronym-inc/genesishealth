import os
from django.core.wsgi import get_wsgi_application

if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'genesishealth.conf.environments.vagrant'

application = get_wsgi_application()