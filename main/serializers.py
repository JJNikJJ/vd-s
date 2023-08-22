import locale
from rest_framework import serializers
from .models import *


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ('id', 'address', 'time', 'latitude', 'longitude')

    time = serializers.SerializerMethodField()

    def get_time(self, obj):
        return f"{obj.work_time_start.strftime('%H:%M')} - {obj.work_time_end.strftime('%H:%M')}"


class PaymentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentType
        fields = ('id', 'title')

    title = serializers.CharField(source='name')


class UserDiscountsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceUserLoyalty
        fields = ('id', 'title', 'visits')

    title = serializers.CharField(source='service.name')
    visits = serializers.IntegerField(source='loyalty_count')


class CheckoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Checkout
        fields = ('id', 'address', 'time', 'servicesList')

    address = serializers.CharField(source='address.address')
    servicesList = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()

    def get_time(self, obj):
        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        formatted_datetime = obj.target_datetime.strftime('%d %B, %H:%M').replace('.', '').replace(' 0', ' ')
        return formatted_datetime

    def get_servicesList(self, obj):
        class CarClassHasServicePriceSerializer(serializers.ModelSerializer):
            class Meta:
                model = CarClassHasServicePrice
                fields = ('id', 'title', 'price')

            title = serializers.CharField(source='servicePrice.service.name')
            id = serializers.IntegerField(source='servicePrice.service.id')

        service_prices = obj.services_list.all()
        return CarClassHasServicePriceSerializer(service_prices, many=True).data
