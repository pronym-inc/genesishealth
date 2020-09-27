from django.conf.urls import url

from genesishealth.apps.nursing_queue.views.nursing_queue import nursing_queue_view
from genesishealth.apps.nursing_queue.views.nursing_queue_entry_complete import nursing_queue_entry_complete_view
from genesishealth.apps.nursing_queue.views.nursing_queue_entry_reschedule import nursing_queue_entry_reschedule_view


urlpatterns = [
    url(
        r'^$',
        nursing_queue_view,
        name="queue"
    ),
    url(
        r'(?P<nursing_queue_entry_id>\d+)/reschedule/$',
        nursing_queue_entry_reschedule_view,
        name="entry-reschedule"
    ),
    url(
        r'(?P<nursing_queue_entry_id>\d+)/complete/$',
        nursing_queue_entry_complete_view,
        name="entry-complete"
    )
]
