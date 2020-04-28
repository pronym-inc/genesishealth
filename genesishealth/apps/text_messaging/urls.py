from django.conf.urls import url

from genesishealth.apps.text_messaging.views.send_group_text import (
    main as send_group_text)


urlpatterns = [
    url(r'^send_group_text/(?P<company_id>\d+)/$',
        send_group_text,
        name="send-group-text"),
]
