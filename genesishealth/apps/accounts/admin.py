from django.contrib import admin
from genesishealth.apps.accounts.models import (
    ProfessionalProfile, PatientProfile, Company, Payor, GenesisGroup)
from genesishealth.apps.accounts.models.admin_user import (
    AdminProfile, AdminPermission, AdminPermissionGroup)


admin.site.register(ProfessionalProfile)
admin.site.register(PatientProfile)
admin.site.register(Company)
admin.site.register(Payor)
admin.site.register(GenesisGroup)
admin.site.register(AdminPermission)
admin.site.register(AdminPermissionGroup)


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    filter_horizontal = ('permissions', 'permission_groups')
