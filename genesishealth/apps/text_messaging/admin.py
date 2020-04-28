from django.contrib import admin

from solo.admin import SingletonModelAdmin

from genesishealth.apps.text_messaging.models import TextMessagingConfiguration


admin.site.register(TextMessagingConfiguration, SingletonModelAdmin)
