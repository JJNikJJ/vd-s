from django.contrib import admin
from .models import *

admin.site.register(CarClass)
admin.site.register(Address)
admin.site.register(Service)
admin.site.register(Car)
admin.site.register(Checkout)
admin.site.register(ServiceUserLoyalty)
admin.site.register(PaymentType)


class CustomUserAdmin(admin.ModelAdmin):
    pass


class PriceLinkAdminInline(admin.TabularInline):
    model = CarClassHasServicePrice
    extra = 1


@admin.register(ServicePrice)
class ServicePriceAdmin(admin.ModelAdmin):
    list_display = ('service', 'address')
    inlines = (PriceLinkAdminInline,)


admin.site.register(CustomUser, CustomUserAdmin)
