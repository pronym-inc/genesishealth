from django.conf.urls import url

from genesishealth.apps.work_queue.views.approve import approve_work_queue_item
from genesishealth.apps.work_queue.views.delay import delay_work_queue_item
from genesishealth.apps.work_queue.views.main import main_queue
from genesishealth.apps.work_queue.views.view import view_work_queue_item


urlpatterns = [
    url(r'^$',
        main_queue,
        name="main-queue"),
    url(r'^(?P<item_id>\d+)/$',
        view_work_queue_item,
        name="view-item"),
    url(r'^(?P<item_id>\d+)/approve/$',
        approve_work_queue_item,
        name="approve-item"),
    url(r'^(?P<item_id>\d+)/delay/$',
        delay_work_queue_item,
        name="delay-item"),
]
