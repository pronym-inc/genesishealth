import os

from celery import Celery

# set the default Django settings module for the 'celery' program.
from celery.schedules import crontab

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE', 'genesishealth.conf.environments.vagrant')

app = Celery('genesishealth_celery')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Set up recurring tasks
app.conf.beat_schedule = {
    'check_refills': {
        'task': 'genesishealth.apps.orders.tasks.check_refills',
        'schedule': crontab(hour='0,12', minute='0')
    }
}
