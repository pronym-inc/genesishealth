from django.contrib import admin
# from django.contrib.admin import SimpleListFilter
from django.contrib.auth.models import User

from genesishealth.apps.gdrives.models import (
    GDrive, GDriveFirmwareVersion, GDriveModuleVersion,
    PharmacyPartner)


class GDriveAdmin(admin.ModelAdmin):
    readonly_fields = ('meid', 'created_at', 'assigned_at', 'device_type')
    list_filter = ('professional',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "professional":
            kwargs["queryset"] = User.objects.filter(
                groups__name="Professional")
        elif db_field.name == "patient":
            kwargs["queryset"] = User.objects.filter(groups__name="Patient")
        return super(GDriveAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)


admin.site.register(GDrive, GDriveAdmin)
admin.site.register(GDriveFirmwareVersion)
admin.site.register(GDriveModuleVersion)
admin.site.register(PharmacyPartner)
