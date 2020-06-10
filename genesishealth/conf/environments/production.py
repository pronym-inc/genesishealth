from genesishealth.conf.generic.settings import *  # noqa


DEBUG = False
DEBUG_STATIC_FILES = False
DEBUG_TRANSMISSION_LOG = False

SITE_URL = 'myghr.genesishealthtechnologies.com'
ALLOWED_HOSTS = [
    'aws-myghr.genesishealthtechnologies.com',
    'myghr.genesishealthtechnologies.com',
    'myghr-prod.genesishealthtechnologies.com',
    'myhealth.genesishealthtechnologies.com'
]

if USE_SQS:
    BROKER_TRANSPORT_OPTIONS = {"quote_name_prefix": 'production-'}


REMOTE_ACCESS_SSH_KEY_PATH = '/home/genesishealth/e2e_key'
REMOTE_ACCESS_SSH_USERNAME = 'ubuntu'
AUTORESTART_COMMAND = 'sudo systemctl restart supervisord'

READING_SERVER_INTERNAL_LOCATIONS = {
    'reading1.genesishealthtechnologies.com': 'reading1.ght-plumbing.in',
    'reading2.genesishealthtechnologies.com': 'reading2.ght-plumbing.in',
    'reading3.genesishealthtechnologies.com': 'reading3.ght-plumbing.in'
}
