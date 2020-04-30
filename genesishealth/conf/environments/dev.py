from genesishealth.conf.generic.settings import *  # noqa


DEBUG = True
DEBUG_STATIC_FILES = True

SITE_URL = 'dev-myghr.genesishealthtechnologies.com'
ALLOWED_HOSTS = ['dev-myghr.genesishealthtechnologies.com', 'dev-aws-myghr.genesishealthtechnologies.com']

if USE_SQS:
    BROKER_TRANSPORT_OPTIONS = {"quote_name_prefix": 'dev-'}
