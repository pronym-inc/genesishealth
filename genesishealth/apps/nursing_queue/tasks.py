from celery import shared_task

from genesishealth.apps.nursing_queue.service import NursingQueueService


@shared_task
def populate_queue():
    service = NursingQueueService()
    service.populate()
