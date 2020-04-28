from django.conf.urls import url

from genesishealth.apps.readings.views.reports.exception import (
    main as exception_report)


urlpatterns = [
    url(r'^exceptions/$', exception_report, name="exception-report")
]
