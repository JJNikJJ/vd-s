from django.contrib import admin
from .models import *

admin.site.register(CarClass)
admin.site.register(Address)
admin.site.register(Service)
admin.site.register(Car)
admin.site.register(ServicePrice)
admin.site.register(Checkout)
admin.site.register(ServiceUserLoyalty)
admin.site.register(PaymentType)


class CustomUserAdmin(admin.ModelAdmin):
    pass


admin.site.register(CustomUser, CustomUserAdmin)
