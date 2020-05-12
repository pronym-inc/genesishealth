from genesishealth.conf.generic.settings import *  # noqa


DEBUG = False
DEBUG_STATIC_FILES = False
DEBUG_TRANSMISSION_LOG = False

SITE_URL = 'aws-myghr.genesishealthtechnologies.com'
ALLOWED_HOSTS = [
    'aws-myghr.genesishealthtechnologies.com',
    'myghr.genesishealthtechnologies.com',
    'myghr-prod.genesishealthtechnologies.com']

if USE_SQS:
    BROKER_TRANSPORT_OPTIONS = {"quote_name_prefix": 'production-'}
