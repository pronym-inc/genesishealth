from django.contrib import admin
from django.urls import reverse
from django.http import HttpResponseRedirect

from django_object_actions import DjangoObjectActions

from genesishealth.apps.api.models import (
    APIFlatfileConnection, APILocation, APIPartner)


class APILocationInline(admin.TabularInline):
    model = APILocation


class APIPartnerAdmin(DjangoObjectActions, admin.ModelAdmin):
    def generate_wellness_document(self, request, obj):
        wellness_doc_url = reverse('api:wellness_doc', args=[obj.pk])
        return HttpResponseRedirect(wellness_doc_url)
    generate_wellness_document.label = "Generate Wellness Doc"

    model = APIPartner
    inlines = [APILocationInline, ]
    change_actions = ['generate_wellness_document']


admin.site.register(APIPartner, APIPartnerAdmin)
admin.site.register(APIFlatfileConnection)
