from django.contrib import admin

from genesishealth.apps.work_queue.models import WorkQueueProfile, WorkQueueType

admin.site.register(WorkQueueProfile)
admin.site.register(WorkQueueType)
