import logging

from celery.task import task

alert_logger = logging.getLogger('alerts')


@task
def trigger_alert(alert, **details):
    alert.trigger_delayed(**details)


@task
def trigger_reminder(reminder, **details):
    reminder.trigger_delayed(**details)
