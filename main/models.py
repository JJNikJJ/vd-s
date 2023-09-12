import datetime
import requests

from django.contrib.auth.models import AbstractUser, User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from vodoleyProjectBot.config import TOKEN


def SendMessage(user, message):
    try:
        chat = UserChat.objects.get(telegram=user.telegram).chat
        send_text = 'https://api.telegram.org/bot' + TOKEN +\
                    '/sendMessage?chat_id=' + chat + '&parse_mode=Markdown&text='\
                    + message
        requests.get(send_text)
        print(f'Message sent to {chat}')
        return True
    except UserChat.DoesNotExist or requests.exceptions.RequestException as e:
        print(f"Cannot send message: {str(e)}")
        return False


class UserChat(models.Model):
    telegram = models.CharField(null=False, max_length=255, verbose_name="Никнейм тг", editable=False)
    chat = models.CharField(null=False, max_length=255, verbose_name="Айди чата", editable=False)

    def __str__(self):
        return f"({self.id}) {self.telegram} #{self.chat}"

    class Meta:
        verbose_name = "Чат"
        verbose_name_plural = "Чаты"


class CarClass(models.Model):
    name = models.CharField(max_length=100, null=False, verbose_name="Название класса авто")

    def __str__(self):
        return f"({self.id}) {self.name}"

    class Meta:
        verbose_name = "Класс авто"
        verbose_name_plural = "Классы авто"


class Address(models.Model):
    latitude = models.FloatField(null=False, default=0, verbose_name="Широта точки на карте")
    longitude = models.FloatField(null=False, default=0, verbose_name="Долгота точки на карте")
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
    mark = models.CharField(max_length=100, null=False, default='', verbose_name="Марка авто")
    model = models.CharField(max_length=100, null=False, default='', verbose_name="Модель авто")
    number = models.CharField(max_length=100, null=False, verbose_name="Номер авто")
    car_class = models.ForeignKey(CarClass, on_delete=models.SET_NULL, null=True, verbose_name="Класс авто")

    def __str__(self):
        return f"({self.id}) {self.mark} {self.model} #{self.number}"

    class Meta:
        verbose_name = "Авто"
        verbose_name_plural = "Авто"


class CustomUser(AbstractUser):
    username = models.CharField(max_length=150, unique=True, verbose_name="ФИО")
    car = models.ForeignKey(Car, on_delete=models.SET_NULL, null=True, verbose_name="Авто")
    telegram = models.CharField(max_length=100, null=True, verbose_name="Телеграм никнейм")
    phone_number = models.CharField(max_length=20, null=True, verbose_name="Номер телефона")
    is_registration_complete = models.BooleanField(default=False, editable=False,
                                                   verbose_name="Регистрация подтверждена")

    bot_welcome_message_sent = models.BooleanField(default=False)
    bot_registration_complete_message_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"({self.id}) {self.username}"

    def save(self, *args, **kwargs):
        self.is_registration_complete = bool(self.car and self.car.car_class)

        # Сообщение о том что регистрация будет подтверждена
        if not self.bot_welcome_message_sent:
            sent = SendMessage(self, "Отлично! Спасибо, что присоединились к нашему сервису. В течение 24 часов мы подтвердим вашу регистрацию, после чего вы получите полный доступ к сервису")
            self.bot_welcome_message_sent = sent

        # Сообщение о том что регистрация подтверждена
        if not self.bot_registration_complete_message_sent\
                and self.is_registration_complete:
            sent = SendMessage(self, "Регистрация подтверждена! Запишитесь на мойку прямо сейчас")
            self.bot_registration_complete_message_sent = sent
        super(CustomUser, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class ServicePrice(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, null=False, verbose_name="Услуга")
    address = models.ForeignKey(Address, on_delete=models.CASCADE, null=False, verbose_name="Адрес автомойки")
    priceLink = models.ManyToManyField(CarClass, through='CarClassHasServicePrice', related_name='%(class)s_link')

    def __str__(self):
        return f"({self.id}) Услуга \"{self.service.name}\" по адресу \"{self.address.address}\""

    class Meta:
        verbose_name = "Стоимость услуги"
        verbose_name_plural = "Стоимости услуг"


class CarClassHasServicePrice(models.Model):
    servicePrice = models.ForeignKey(ServicePrice, on_delete=models.CASCADE, null=False, verbose_name="Стоимость услуги")
    carClass = models.ForeignKey(CarClass, on_delete=models.CASCADE, null=False, verbose_name="Класс автомобиля")
    price = models.FloatField(validators=[MinValueValidator(0.0)], verbose_name="Стоимость услуги")

    def __str__(self):
        return f"({self.id}) Услуга \"{self.servicePrice.service}\" для \"{self.carClass}\""

    class Meta:
        verbose_name = "Стоимость по классу авто"
        verbose_name_plural = "Стоимость по классу авто"


class PaymentType(models.Model):
    name = models.CharField(default="", max_length=100, null=False, verbose_name="Наименование")
    discount = models.FloatField(default=0.0,
                                 verbose_name="Скидка при этом способе оплаты",
                                 validators=[
                                     MaxValueValidator(1),
                                     MinValueValidator(0)
                                 ])

    def __str__(self):
        return f"({self.id}) {self.name}"

    class Meta:
        verbose_name = "Способ оплаты"
        verbose_name_plural = "Способы оплаты"


class Checkout(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, verbose_name="Заказчик услуг")
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, verbose_name="Адрес заказанных услуг")
    services_list = models.ManyToManyField(CarClassHasServicePrice, verbose_name="Заказанные услуги")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания заказа")
    target_datetime = models.DateTimeField(null=True, default=None,
                                           verbose_name="Время, на которое была назначена запись")
    status = models.BooleanField(default=False, verbose_name="Заказ был завершен")
    canceled = models.BooleanField(default=False, verbose_name="Заказ был отменен")
    postponed = models.BooleanField(default=False, verbose_name="Заказ был отложен")
    final_price = models.FloatField(validators=[MinValueValidator(0.0)], verbose_name="Полная стоимость заказа")
    user_review = models.CharField(max_length=200, null=True, blank=True, default="", verbose_name="Отзыв клиента")
    payment_type = models.ForeignKey(PaymentType, null=True, on_delete=models.SET_NULL, verbose_name="Способ оплаты")
    bonuses_received = models.BooleanField(default=False,
                                           verbose_name="Бонусы по пограмме лояльности были начислены",
                                           editable=False)

    def save(self, *args, **kwargs):
        if self.status and not self.bonuses_received and not self.canceled:
            for service_price in self.services_list.all():
                service = service_price.servicePrice.service
                if service.has_loyalty:
                    try:
                        loyal = ServiceUserLoyalty.objects.get(user=self.user, service=service)
                        loyal.loyalty_count += 1
                        if loyal.loyalty_count > 3:
                            loyal.loyalty_count = 0
                    except ServiceUserLoyalty.DoesNotExist:
                        loyal = ServiceUserLoyalty.objects.create(user=self.user, service=service, loyalty_count=1)
                    loyal.save()
            self.bonuses_received = True

        super(Checkout, self).save(*args, **kwargs)

    @property
    def is_past_due(self):
        return datetime.date.today() > self.target_datetime.date()

    def __str__(self):
        username = "<???>" if not self.user else self.user.username
        return f"({self.id}) Заказ от {username}"

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

