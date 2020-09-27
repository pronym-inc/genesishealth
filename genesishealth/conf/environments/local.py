from genesishealth.conf.generic.settings import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ['*']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
        }
    }
}

COMPRESS_ENABLED = False
SITE_URL = '127.0.0.1:8000'