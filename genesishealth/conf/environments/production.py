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
STAMPS_FAKE_LABEL_URL = f"https://{SITE_URL}/static/img/fake_label.png"
