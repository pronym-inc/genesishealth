from genesishealth.conf.generic.settings import *  # noqa


DEBUG = True
DEBUG_STATIC_FILES = True

SITE_URL = 'genesishealth.local'
ALLOWED_HOSTS = ['genesishealth.local']

if USE_SQS:
    BROKER_TRANSPORT_OPTIONS = {"quote_name_prefix": 'vagrant-'}


RAISE_ON_500 = True
USE_HTTPS = False

READING_SERVER_LOCATIONS = ('localhost',)

LOGGING['loggers']['django.request']['handlers'] = ['console']
