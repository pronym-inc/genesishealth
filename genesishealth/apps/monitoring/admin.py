from django.contrib import admin

from genesishealth.apps.monitoring.models import (
    DatabaseServer, ReadingServer, WebServer, WorkerServer)


for m in (DatabaseServer, ReadingServer, WebServer, WorkerServer):
    admin.site.register(m)
