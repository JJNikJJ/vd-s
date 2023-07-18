import datetime

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models


class CarClass(models.Model):
    name = models.CharField(max_length=100, null=False, verbose_name="Название класса авто")

    def __str__(self):
        return f"({self.id}) {self.name}"

    class Meta:
        verbose_name = "Класс авто"
        verbose_name_plural = "Классы авто"


class Address(models.Model):
    map_coordinates = models.CharField(max_length=100, null=False, verbose_name="Координаты на карте")
    address = models.CharField(max_length=100, null=False, verbose_name="Адрес автомойки")
    work_time_start = models.TimeField(null=False, default=datetime.time(9, 0),
                                       verbose_name="Время начала работы автомойки")
    work_time_end = models.TimeField(null=False, default=datetime.time(22, 0),
                                     verbose_name="Время конца работы автомойки")

    def __str__(self):
        return f"({self.id}) {self.address}"

    class Meta:
        verbose_name = "Адрес автомойки"
        verbose_name_plural = "Адреса автомоек"


class Service(models.Model):
    name = models.CharField(max_length=100, null=False, verbose_name="Название услуги")
    is_special = models.BooleanField(default=False, verbose_name="Услуга является специальной")
    has_loyalty = models.BooleanField(default=False, verbose_name="Участвует в программе лояльности")

    def __str__(self):
        return f"({self.id}) {self.name}"

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"


class Car(models.Model):
    name = models.CharField(max_length=100, null=False, verbose_name="Марка и модель авто")
    number = models.CharField(max_length=100, null=False, verbose_name="Номер авто")
    car_class = models.ForeignKey(CarClass, on_delete=models.SET_NULL, null=True, verbose_name="Класс авто")

    def __str__(self):
        return f"({self.id}) {self.name} #{self.number}"

    class Meta:
        verbose_name = "Авто"
        verbose_name_plural = "Авто"


class CustomUser(AbstractUser):
    car = models.ForeignKey(Car, on_delete=models.SET_NULL, null=True, verbose_name="Авто")
    telegram = models.CharField(max_length=100, null=True, verbose_name="Телеграм никнейм")
    phone_number = models.CharField(max_length=20, null=True, verbose_name="Номер телефона")

    def __str__(self):
        return f"({self.id}) {self.username}"

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class ServicePrice(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, null=False, verbose_name="Услуга")
    address = models.ForeignKey(Address, on_delete=models.CASCADE, null=False, verbose_name="Адрес автомойки")
    car_class = models.ForeignKey(CarClass, on_delete=models.CASCADE, null=False, verbose_name="Класс авто")
    price = models.FloatField(validators=[MinValueValidator(0.0)], verbose_name="Стоимость услуги")

    def __str__(self):
        return f"({self.id}) Услуга \"{self.service.name}\" по адресу \"{self.address.address}\" для класса авто \"{self.car_class.name}\""

    class Meta:
        verbose_name = "Стоимость услуги"
        verbose_name_plural = "Стоимости услуг"


class PaymentType(models.Model):
    name = models.CharField(default="", max_length=100, null=False, verbose_name="Наименование")

    def __str__(self):
        return f"({self.id}) {self.name}"

    class Meta:
        verbose_name = "Способ оплаты"
        verbose_name_plural = "Способы оплаты"


class Checkout(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, verbose_name="Заказчик услуг")
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, verbose_name="Адрес заказанных услуг")
    services_list = models.ManyToManyField(ServicePrice, verbose_name="Заказанные услуги")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания заказа")
    target_datetime = models.DateTimeField(null=True, default=None,
                                           verbose_name="Время, на которое была назначена запись")
    status = models.BooleanField(default=False, verbose_name="Заказ был завершен")
    postponed = models.BooleanField(default=False, verbose_name="Заказ был отложен")
    final_price = models.FloatField(validators=[MinValueValidator(0.0)], verbose_name="Полная стоимость заказа")
    user_review = models.CharField(max_length=200, null=True, verbose_name="Отзыв заказчика")
    payment_type = models.ForeignKey(PaymentType, null=True, on_delete=models.SET_NULL, verbose_name="Способ оплаты")

    def __str__(self):
        return f"({self.id}) Заказ от \"{self.user.username}\" на дату \"{self.target_datetime.date()}\""

    class Meta:
        verbose_name = "Заказ услуги"
        verbose_name_plural = "Заказы услуг"


class ServiceUserLoyalty(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=False, verbose_name="Заказчик")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, null=False, verbose_name="Услуга")
    loyalty_count = models.IntegerField(null=False, default=0, verbose_name="Кол-во совершенных заказов")

    def __str__(self):
        return f"({self.id}) Лояльность по услуге \"{self.service.name}\" для {self.user.username}"

    class Meta:
        verbose_name = "Лояльность пользователя"
        verbose_name_plural = "Лояльности пользователей"

