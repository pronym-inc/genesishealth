from django.contrib import admin

from .models import (
    CommunicationCategory, CommunicationStatus, CommunicationSubcategory,
    DeactivationReason, DeviceProblem, MeterDisposition,
    CommunicationResolution, OrderProblemCategory)


admin.site.register(CommunicationCategory)
admin.site.register(CommunicationResolution)
admin.site.register(CommunicationStatus)
admin.site.register(CommunicationSubcategory)
admin.site.register(DeactivationReason)
admin.site.register(DeviceProblem)
admin.site.register(MeterDisposition)
admin.site.register(OrderProblemCategory)
