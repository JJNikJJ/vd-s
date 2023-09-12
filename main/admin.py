from django.contrib import admin
from main.models import *
from main.forms import CheckoutAdminForm

admin.site.register(CarClass)
admin.site.register(Address)
admin.site.register(ServiceUserLoyalty)
admin.site.register(PaymentType)


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'telegram', 'is_registration_complete']
    list_filter = ['is_registration_complete']
    readonly_fields = ['is_registration_complete',
                       # 'bot_registration_complete_message_sent',
                       # 'bot_welcome_message_sent'
                       ]

    def is_registration_complete(self, obj):
        return "Да" if obj.is_registration_complete else "Нет"


admin.site.register(CustomUser, CustomUserAdmin)


class CheckoutAdmin(admin.ModelAdmin):
    form = CheckoutAdminForm
    list_display = ['__str__', 'target_datetime', 'checkout_status']
    # TODO: readonly fields
    readonly_fields = ['bonuses_received',
                       # 'canceled', 'postponed'
                       ]
    list_filter = ['status']

    def checkout_status(self, obj):
        if obj.canceled:
            return "Отменен"
        if obj.status:
            return "Завершен"
        elif obj.is_past_due:
            return "Просрочен"
        else:
            return "Активен"

    checkout_status.short_description = "Статус"


admin.site.register(Checkout, CheckoutAdmin)


class UserChatAdmin(admin.ModelAdmin):
    readonly_fields = ['telegram', 'chat']


admin.site.register(UserChat, UserChatAdmin)


class PriceLinkAdminInline(admin.TabularInline):
    model = CarClassHasServicePrice
    extra = 1


@admin.register(ServicePrice)
class ServicePriceAdmin(admin.ModelAdmin):
    list_display = ['service', 'address']
    inlines = (PriceLinkAdminInline,)


class CarAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'car_class']
    list_filter = ['car_class']


admin.site.register(Car, CarAdmin)


class ServiceAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'is_special', 'has_loyalty']
    list_filter = ['is_special', 'has_loyalty']


admin.site.register(Service, ServiceAdmin)
