import json
import os

from datetime import date

from django.conf.global_settings import STATICFILES_FINDERS

from kombu.utils.url import safequote

secrets_path = '/etc/secrets.json'
secrets = json.load(open(secrets_path))

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VIRTUALENV_DIR = os.path.dirname(os.path.dirname(os.path.dirname(BASE_DIR)))
VAR_DIR = os.path.join(VIRTUALENV_DIR, 'var')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = secrets['django_secret']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']

USE_TZ = True
TIME_ZONE = 'America/Chicago'
# Application definition

INSTALLED_APPS = [
    'django_object_actions',
    'django.contrib.admin',
    'genesishealth.apps.utils.auth_app_config.AuthAppConfig',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'solo',
    'genesishealth.apps.accounts',
    'genesishealth.apps.api',
    'genesishealth.apps.dashboard',
    'genesishealth.apps.gdrives',
    'genesishealth.apps.readings',
    'genesishealth.apps.health_information',
    'genesishealth.apps.reports',
    'genesishealth.apps.utils',
    'gunicorn',
    'genesishealth.apps.contact',
    'genesishealth.apps.heartbeat',
    'genesishealth.apps.audit',
    'genesishealth.apps.logs',
    'genesishealth.apps.alerts',
    'genesishealth.apps.monitoring',
    'genesishealth.apps.dropdowns',
    'genesishealth.apps.products',
    'genesishealth.apps.orders',
    'genesishealth.apps.pharmacy',
    'genesishealth.apps.ghtadmin',
    'genesishealth.apps.epc',
    'genesishealth.apps.nursing',
    'genesishealth.apps.text_messaging',
    'compressor',
    'localflavor',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'genesishealth.apps.utils.middleware.StoreSessionHistoryMiddleware',
    'genesishealth.apps.utils.middleware.LastTouchedMiddleware',
    'genesishealth.apps.utils.middleware.SecurityRedirectMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware'
]

ROOT_URLCONF = 'genesishealth.conf.urls.main'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'genesishealth.conf.wsgi.app.application'


# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': secrets['db_host'],
        'NAME': secrets['db_name'],
        'USER': secrets['db_username'],
        'PASSWORD': secrets['db_password']
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

USE_SQS = secrets.get('use_sqs', False)

if USE_SQS:
    CELERY_BROKER_URL = "sqs://{0}:{1}@".format(
        safequote(secrets['aws_access_key']),
        safequote(secrets['aws_secret_key'])
    )
else:
    # If not using SQS, expect a local redis queue.
    CELERY_BROKER_URL = 'redis://localhost:6379/0'

# Logging
LOG_PATH = os.path.join(VIRTUALENV_DIR, 'var/log/django/genesishealth.log')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': LOG_PATH,
        },
    },
    'loggers': {
        'doctors': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

LOGIN_URL = '/accounts/login/'
LOGOUT_URL = '/accounts/logout/'
LOGIN_REDIRECT_URL = '/dashboard/'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATICFILES_FINDERS += (
    'compressor.finders.CompressorFinder',
)

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

VAR_ROOT = os.path.join(VIRTUALENV_DIR, 'var')

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(VIRTUALENV_DIR, 'var/static')
MEDIA_URL = '/uploads/'
MEDIA_ROOT = os.path.join(VIRTUALENV_DIR, 'var/media')

ADMIN_MEDIA_PREFIX = '/static/admin/'
LOG_PATH = os.path.join(VAR_ROOT, 'log')

DEBUG_STATIC_FILES = True
TOKEN_EXPIRATION_MINUTES = 120
API_SECRET = secrets['api_secret']

DEFAULT_FROM_EMAIL = 'admin@genesishealth.com'
USE_COMPILED_JS = False
COMPILED_JS_URL = '/packagedjs/'

GDRIVE_READING_PORT = 443
GDRIVE_TCP_SIMULTANEOUS_CONNECTIONS = 128

AES_KEY = secrets.get('aes_key', '')
PUBLIC_IP_CHECK_URL = 'http://checkip.dyndns.com/'

COMPRESS_OFFLINE = True

COMPRESS_CSS_FILTERS = (
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.CSSMinFilter',
)

COMPRESS_ENABLED = True

TWILIO_API_VERSION = '2010-04-01'
TWILIO_SID = secrets.get('twilio_sid', '')
TWILIO_TOKEN = secrets.get('twilio_token', '')
TWILIO_CALLERID = secrets.get('twilio_callerid', '')

ACCOUNT_ACTIVATION_DAYS = 7

EMAIL_BACKEND = "sgbackend.SendGridBackend"
SENDGRID_API_KEY = secrets.get('sendgrid_api_key')

DEFAULT_FROM_EMAIL = 'no-reply@genesishealthtechnologies.com'

SHIPMENT_NOTIFICATION_EMAILS = [
    #TODO: Fill this in
    "gregg@pronym.com",
]

APIS_AVAILABLE = {
    'pushDataFromVendor': {
        'humanReadableName' : 'Push Data From Vendor',
        'url' : '/apis/push_observations/',
    }
}

DEVICE_TYPE = 'genesis-glu'

P3P_COMPACT = 'CP="CAO DSP CURa ADMa DEVa TAIa CONa OUR DELa BUS IND PHY ONL UNI PUR COM NAV DEM STA"'

DASHBOARD_PREFIX = '/dashboard/#'

ALERT_WAIT_INTERVAL = 60 * 60 * 24 * 7 # 1 Week

SERVICE_URI = 'http://service.genesishealthtechnologies.com/'

TABLE_ACTION_ICON_CLASSES = {
    'accounts:manage-login': 'icon-key',
    'accounts:manage-user': 'icon-signin',
    'accounts:manage-professionals-message': 'icon-comments',
    'accounts:manage-patients-notes': 'icon-file',
    'accounts:manage-companies-edit': 'icon-star',
    'accounts:manage-demo-edit': 'icon-user',
    'accounts:manage-groups-patients-edit': 'icon-user',
    'accounts:manage-patients-records': 'icon-folder-open',
    'accounts:manage-patients-edit': 'icon-user',
    'accounts:manage-payors-edit': 'icon-money',
    'accounts:manage-groups-payors-edit': 'icon-pencil',
    'accounts:manage-professionals-edit': 'icon-briefcase',
    'accounts:manage-professionals-patients': 'icon-user',
    'accounts:manage-patients-reminders': 'icon-exclamation-sign',
    'accounts:manage-groups-edit': 'icon-group',
    'accounts:manage-groups-relationships': 'icon-user-md',
    'accounts:manage-groups-professionals': 'icon-briefcase',
    'accounts:manage-groups-patients': 'icon-user',
    'accounts:manage-groups-payors': 'icon-money',
    'accounts:manage-groups-companies': 'icon-star',
    'accounts:manage-groups-devices': 'icon-hdd',
    'accounts:manage-groups-demo': 'icon-cogs',
    'accounts:manage-groups-demo-edit': 'icon-user',
    'accounts:manage-groups-reports': 'icon-folder-open',
    'accounts:manage-patients-detail': 'icon-user',
    'accounts:manage-groups-detail': 'icon-group',
    'accounts:manage-professionals-detail': 'icon-briefcase',
    'alerts:alerts-edit': 'icon-pencil',
    'gdrives:edit': 'icon-hdd',
    'gdrives:delete': 'icon-trash',
    'reports:patient-index': 'icon-bar-chart',
    'reports:scheduled-reports-edit': 'icon-calendar',
    'gdrives:patient-details': 'icon-wrench',
    'gdrives:assign-to-patient': 'fa fa-plus-square',
    'gdrives:unassign': 'fa fa-minus-square',
    'gdrives:detail': 'fa fa-mobile-phone',
    'gdrives:inspect-manufacturer-carton': 'fa fa-eye',
    'gdrives:edit-manufacturer-carton': 'fa fa-dropbox',
    'accounts:communication-report-pdf': 'fa fa-file-text-o',
    'accounts:edit-communication': 'fa fa-pencil-square-o',
    'gdrives:rma-inspection-pdf': 'fa fa-file-text-o',
    'gdrives:edit-complaint': 'fa fa-pencil-square-o',
    'gdrives:manufacturer-carton-pdf': 'fa fa-file-text-o',
    'gdrives:non-conformity-report-pdf': 'fa fa-file-text-o',
    'orders:details': 'fa fa-shopping-basket',
    'orders:claim': 'fa fa-hand-grab-o',
    'orders:edit-shipment': 'fa fa-pencil-square-o',
    'orders:shipment-packing-list': 'fa fa-file-text-o',
    'orders:create-shipment': 'fa fa-send',
    'default': 'icon-certificate',
}


ADMINS = (
    ('Gregg Keithley', 'gregg@pronym.com'),
)

MANAGERS = ADMINS

MAX_ATTEMPTS = MAX_API_ATTEMPTS = 15
MINIMUM_RETRY_DELAY = 3600  # Measured in seconds

APIS_AVAILABLE = {
    'pushDataFromVendor': {
        'humanReadableName': 'Push Data From Vendor',
        'url': '/apis/push_observations/',
        'type': 1
    },
    'registerDevice': {
        'humanReadableName': 'Register Device',
        'url': '/apis/register_device/',
        'type': 2
    },
    'unregisterDevice': {
        'humanReadableName': 'Unregister Device',
        'url': '/apis/unregister_device/',
        'type': 2
    }
}

API_SOURCE_NAME = "genesis_health_technologies"
API_SECRET_KEY = "254f8333-f411-4893-be2a-eea8a339421a"
API_OBSERVATION_TYPE = 'Glucose_Mg'
API_UNIT = 'mg/dl'

GLUCOSE_HI_VALUE = 600
GLUCOSE_LO_VALUE = 20

CONTACT_FORM_FROM_EMAIL = 'admin@genesishealthtechnologies.com'
CONTACT_FORM_EMAIL_RECIPIENTS = ['helpdesk@genesishealthtechnologies.com']
DEFAULT_SETUP_RECIPIENT_EMAIL = 'greggkeithley@gmail.com'

TIME_INPUT_FORMATS = ('%I:%M %p',)
DATE_INPUT_FORMATS = ('%Y-%m-%d', '%m/%d/%Y')
DATETIME_INPUT_FORMATS = ('%m/%d/%Y %I:%M %p',)
DATETIME_FORMAT = 'N d, Y g:i A'

MAX_PRINT_LOGBOOK_ENTRIES = 2
MAX_LOGBOOK_ENTRIES = 50

LOGGED_IN_TIME = 15 * 60

# Enables patient messaging (to and from professional).
ENABLE_PATIENT_MESSAGES = False

# Enables alert functionality site-wide.
ENABLE_ALERTS = False

# Enables medication events on logbook
ENABLE_MEDICATION_EVENT = False

# Enables phone app functionality for alerts.
ENABLE_PHONE_APP_FOR_ALERTS = False

# Enables patient records
ENABLE_PATIENT_RECORDS = False

# Enable scheduled reports
ENABLE_SCHEDULED_REPORTS = False

# Enable reminders
ENABLE_REMINDERS = False

# Enable messages
ENABLE_MESSAGES = False

# If set to True, the end to end test will POST to the service server directly instead
# of sending to the TCP server.
END_TO_END_SKIP_TCP = False

VERSION = '3.0.0'
ENVIRONMENT = 'Production'

# This should NOT vary by environment.  The heartbeat page of every environment needs to know where the
# production server is.
PRODUCTION_HEARTBEAT_URL = 'http://myghr.genesishealthtechnologies.com/heartbeat/'

TCP_SERVERS = ('http://50.57.168.251', 'http://108.166.111.101', 'http://216.70.86.164')

# This is used as the test name for the heartbeat tests.
VERIZON_TEST_USERNAME = '1231we23r2f'

REMOTE_API_HOST = 'http://localhost'
REMOTE_API_PUSH_LOCATION = '%s/biometric/com.verizon.mhealth.bs.BiometricHttpService.cls' % REMOTE_API_HOST

# Decryption key for incoming readings
GDRIVE_DECRYPTION_KEY = AES_KEY
# Socket for 0MQ components to communicate with each other
ZMQ_SOCKET = 'ipc:///tmp/zmq.socket'
# Number of seconds to allow spy process to run
GDRIVE_READING_TIMEOUT = 4
# How many bytes the spy process should read from stdin
GDRIVE_READING_BUFFER_LENGTH = 2048
# How long a reading is
GDRIVE_READING_DATA_LENGTH = 1111
# Options for PDF rendering
WKHTMLTOPDF_CMD_OPTIONS = {'quiet': True}
WKHTMLTOPDF_CMD = 'xvfb-run /usr/bin/wkhtmltopdf'

# Locations of reading servers
READING_SERVER_LOCATIONS = (
    'reading1.genesishealthtechnologies.com',
    'reading2.genesishealthtechnologies.com',
    'reading3.genesishealthtechnologies.com'
)

# Number of rows beginning each CSV file
CSV_NUMBER_OF_HEADER_ROWS = 3

# URLs to forward readings to
READING_FORWARD_URLS = ()

DEBUG_TRANSMISSION_LOG = False

# Format for scalability device names
SCALABILITY_MEID_FORMAT = 'SCTEST000%03d'
SCALABILITY_SERIAL_FORMAT = 'SCATEST0%03d'

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Hour of the day (24 hour clock) that out of date shipments are checked.
CHECK_UPCOMING_SHIPMENT_HOUR = 8

# If set to False, system will not send out emails.
SEND_EMAILS = True

# Spy bind address
SPY_BIND_ADDRESS = ''

DISABLE_VERIZON = True

VERIZON_TIMEOUT = 3

# How long readings should be allowed to be unresolved, for
# audit purposes.
RESOLUTION_ALLOWANCE_TIME = 60

# How far back should we look for audit stuff?
AUDIT_START_DATE = date(2014, 7, 1)

# Support number for GHT
GENESIS_SUPPORT_PHONE_NUMBER = "(888) 263-0003"

HTTP_PROTOCOL = "https"

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
            'builtins': ['genesishealth.apps.utils.templatetags.genesis_tools']
        },
    },
]

REMOTE_ACCESS_SSH_KEY_PASSWORD = None
DISABLE_ALERTS = False

ERROR_EMAIL_RECIPIENTS = ('gregg@pronym.com',)
WARNING_EMAIL_RECIPIENTS = ('gregg@pronym.com',)
E2E_CRITICAL_TEXT_RECIPIENTS = ('3146035479',)
E2E_CRITICAL_THRESHOLD = 3

GOOGLE_MAPS_TIMEZONE_API_KEY = secrets.get('google_maps_timezone_api_key', '')

STAMPS_INTEGRATION_ID = secrets.get('stamps_integration_id', '')
STAMPS_USERNAME = secrets.get('stamps_username')
STAMPS_PASSWORD = secrets.get('stamps_password')
STAMPS_WSDL = 'testing'
STAMPS_FROM_ZIPCODE = '63117'
STAMPS_FROM_ADDRESS = {
    'FullName': "Genesis Health Technologies",
    'Address1': '212 Lone Oak Rd',
    'Address2': '',
    'City': 'Paducah',
    'State': 'KY'
}

CELERY_ACCEPT_CONTENT = ['pickle', 'json', 'msgpack', 'yaml']

PASSWORD_CHANGE_INTERVAL = 90

SKIP_DETECT_TIMEZONE = False

DISABLE_ORDERS = False

TABLE_DEFAULT_AJAX_LIMIT = 10000

DISABLE_STAMPS_LABELS = False

CONNECTIONS_API_USERNAME = 'jcross@genesishealthtechnologies.com'
CONNECTIONS_API_PASSWORD = 'textus138'

SKIP_FORWARD_READINGS = False
