from django.contrib import admin

from genesishealth.apps.orders.models import (
    OrderCategory, ShippingClass, ShippingPackageType)


admin.site.register(OrderCategory)
admin.site.register(ShippingClass)
admin.site.register(ShippingPackageType)
