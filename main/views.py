import json
from datetime import datetime, timedelta
from django.db import DatabaseError
from django.http import JsonResponse
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from background_task import background


from .serializers import *
from .util import get_random_string


class AuthObtainToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token = Token.objects.get_or_create(user=user)
        return JsonResponse({'token': str(token[0])})


class PaymentTypeListView(APIView):
    def get(self, request):
        payment_types = PaymentType.objects.all()
        serializer = PaymentTypeSerializer(payment_types, many=True)
        return JsonResponse(serializer.data, safe=False)


class AddressListView(APIView):
    def get(self, request):
        addresses = Address.objects.all()
        serializer = AddressSerializer(addresses, many=True)
        return JsonResponse(serializer.data, safe=False)


class UserDiscountsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        loyalty_data = ServiceUserLoyalty.objects.filter(user=user)
        loyalty_data = loyalty_data\
            .filter(service__in=Service.objects.filter(has_loyalty=True))\
            .exclude(loyalty_count=0)
        serializer = UserDiscountsSerializer(loyalty_data, many=True)
        return JsonResponse(serializer.data, safe=False)


class UserCheckoutsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        checkouts = Checkout.objects.filter(user=user, status=False, canceled=False)
        serializer = CheckoutSerializer(checkouts, many=True)
        return JsonResponse(serializer.data, safe=False)


class MainPage(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        loyalty_data = ServiceUserLoyalty.objects.filter(user=user)
        loyalty_data = loyalty_data.filter(service__in=Service.objects.filter(has_loyalty=True))
        serializer = UserDiscountsSerializer(loyalty_data, many=True)
        data = {'userName': user.username,
                'userNumber': user.phone_number,
                'discountsList': serializer.data}
        return JsonResponse(data, safe=False)


class GetServicesForAddress(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        address = data.get('addressID')

        user = request.user
        if not user.car or not user.car.car_class:
            return JsonResponse({'message': 'Ошибка: отсутствуют данные об авто пользователя или класс авто не заполнен.'})

        car_class = request.user.car.car_class

        services = ServicePrice.objects.filter(address_id=address)
        data = []
        for service in services:
            price = CarClassHasServicePrice.objects\
                .filter(carClass=car_class, servicePrice=service).first()
            if not price:
                continue
            data.append({'title': service.service.name,
                         'price': price.price,
                         'id': service.id,
                         'type': service.service.is_special})

        return JsonResponse(data, safe=False)


def RegisterUser(request):
    if request.method != 'POST':
        return JsonResponse({'message': 'Ошибка: invalid request method.'})

    data = json.loads(request.body)
    username = data.get('userName')
    user_number = data.get('userNumber')
    user_tg = data.get('userTG')
    mark = data.get('mark')
    model = data.get('model')
    car_number = data.get('carNumber')

    car = Car.objects.create(
        mark=mark,
        model=model,
        number=car_number
    )
    car.save()

    try:
        user = CustomUser.objects.create(
            username=username,
            car=car,
            telegram=user_tg,
            phone_number=user_number
        )
        user.set_password(get_random_string(10))
        user.save()
    except DatabaseError:
        car.delete()
        return JsonResponse({'message': 'Ошибка: user already exists or data is invalid'})

    token = Token.objects.get_or_create(user=user)
    return JsonResponse({'token': str(token[0])})


class CreateCheckout(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.car or not user.car.car_class:
            return JsonResponse({'message': 'Ошибка: отсутствуют данные об авто пользователя или класс авто не заполнен.'})

        car_class = user.car.car_class
        data = json.loads(request.body)
        address = data.get('address')
        time = data.get('time') # 2023-08-16 18:08:20
        payment_type = data.get('paymentType')
        services_list = data.get('servicesList', [])
        discount = data.get('discount')

        services = ServicePrice.objects.filter(id__in=services_list)
        price_sum = 0
        approved = []
        finalServices = []
        takes_time = 0
        for service in services:
            price = CarClassHasServicePrice.objects \
                .filter(carClass=car_class, servicePrice=service).first()
            if not price:
                continue

            service_price = price.price

            if discount:
                try:
                    loyal = ServiceUserLoyalty.objects.get(id=discount, service=service.service).loyalty_count
                    service_price -= service_price * loyal * 0.05
                except ServiceUserLoyalty.DoesNotExist:
                    pass

            price_sum += service_price
            approved.append(service)
            finalServices.append(price)
            takes_time += 10

        if len(approved) == 0:
            return JsonResponse(
                {'message': 'Ошибка: выбранных услуг не существует для текущего класса автомобиля пользователя.'})

        if payment_type:
            try:
                payment = PaymentType.objects.get(id=payment_type)
                if payment.discount > 0:
                    price_sum -= price_sum * payment.discount
            except PaymentType.DoesNotExist:
                pass

        target_datetime = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
        checkout = Checkout.objects.create(
            user=request.user,
            address=Address.objects.get(id=address),
            target_datetime=target_datetime,
            payment_type=PaymentType.objects.get(id=payment_type),
            final_price=price_sum,
            takes_time=takes_time
        )

        try:
            checkout.services_list.set(list(map(lambda x: x.id, finalServices)))
            checkout.save()
        except DatabaseError as e:
            checkout.delete()
            return JsonResponse(
                {'message': f'Ошибка: {str(e)}'})

        task_started = False
        current_time = datetime.datetime.now()
        scheduled_time = target_datetime + timedelta(minutes=takes_time - 10)
        time_difference = scheduled_time - current_time
        if scheduled_time >= current_time:
            notify_user_when_checkout_ends(checkout.id, schedule=time_difference.seconds)
            task_started = True

        return JsonResponse(data={'message': 'OK',
                                  'task started': time_difference if task_started else 'False',
                                  'approved': list(map(lambda x: x.id, approved)),
                                  'finalServices': list(map(lambda x: x.id, finalServices))},
                            safe=False)


class PostponeCheckout(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        checkout_id = data.get('id')

        try:
            checkout = Checkout.objects.get(id=checkout_id)
            if not checkout.postponed:
                date = checkout.target_datetime + timedelta(minutes=15)
                checkout.target_datetime = date
            checkout.postponed = True
            checkout.save()
        except DatabaseError as e:
            return JsonResponse({'message': f'Ошибка: {str(e)}'})

        return JsonResponse({'message': 'OK'})


def LoginUser(request):
    if request.method != 'POST':
        return JsonResponse({'message': 'Ошибка: неправильный метод запроса.'})

    data = json.loads(request.body)
    username = data.get('username')

    if str(username)[0] == '@':
        user_field = 'telegram'
    else:
        user_field = 'phone_number'

    try:
        user = CustomUser.objects.get(**{user_field: username})
    except CustomUser.DoesNotExist:
        return JsonResponse({'message': 'Ошибка: пользователя с введенными данными не существует.'})

    token = Token.objects.get_or_create(user=user)
    return JsonResponse({'message': 'OK', 'token': str(token[0])})


class EditUser(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        if not user:
            return JsonResponse({'message': 'Ошибка: пользователь не найден в данных сессии.'})

        mark = ''
        model = ''
        number = ''
        completed = False
        if user.car:
            mark = user.car.mark
            model = user.car.model
            number = user.car.number
            if user.car.car_class:
                completed = True
        data = {
            "userName": user.username,
            "userNumber": user.phone_number,
            "userTG": user.telegram,
            "mark": mark,
            "model": model,
            "carNumber": number,
            "completed": completed
        }

        return JsonResponse(data, safe=False)

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        username = data.get('userName')
        user_number = data.get('userNumber')
        user_tg = data.get('userTG')
        mark = data.get('mark')
        model = data.get('model')
        car_number = data.get('carNumber')

        user = request.user
        user.username = username
        user.phone_number = user_number
        user.telegram = user_tg
        car = user.car
        if car:
            if car.mark != mark or car.model != model:
                car.car_class = None
            car.mark = mark
            car.model = model
            car.number = car_number
        else:
            car = Car.objects.create(mark=mark, model=model, number=car_number)
            user.car = car

        car.save()
        user.save()

        return JsonResponse({'message': 'OK'})


class CancelCheckout(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        checkout_id = data.get('id')

        try:
            checkout = Checkout.objects.get(id=checkout_id)
            checkout.canceled = True
            checkout.save()
        except DatabaseError as e:
            return JsonResponse({'message': f'Ошибка: {str(e)}'})

        return JsonResponse({'message': 'OK'})


class EditCheckout(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        checkout_id = data.get('id')
        address = data.get('address')
        new_time = datetime.datetime.strptime(data.get('time'), '%Y-%m-%d %H:%M:%S')

        try:
            checkout = Checkout.objects.get(id=checkout_id)
            checkout.address = Address.objects.get(id=address)
            checkout.target_datetime = new_time
            checkout.save()
        except DatabaseError as e:
            return JsonResponse({'message': f'Ошибка: {str(e)}'})

        return JsonResponse({'message': 'OK'})


class GetAddressTimings(APIView):

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        address_id = data.get('id')
        target_date = data.get('date')

        address = Address.objects.get(id=address_id)
        checkouts = Checkout.objects.filter(address=address, target_datetime__date=target_date)

        service_timings = [
            {
                'id': entity.id,
                'start': entity.target_datetime.time(),
                'takes': entity.takes_time,
            }
            for entity in checkouts
        ]

        data = get_time_slices(address.slots_amount, address.work_time_start, address.work_time_end, service_timings)

        return JsonResponse(data, safe=False)


def get_time_slices(max_slots, start_time, end_time, service_timings):
    time_slices = []
    ten_minutes = timedelta(minutes=10)
    current_time = datetime.datetime.combine(datetime.datetime.today(), start_time)
    end_time = datetime.datetime.combine(datetime.datetime.today(), end_time)
    exclude_slots = {}

    for service in service_timings:
        service_start = datetime.datetime.combine(datetime.datetime.today(), service['start'])
        service_end = service_start + timedelta(minutes=service['takes'])
        while service_start < service_end:
            timestr = service_start.time().strftime('%H:%M')
            if timestr in exclude_slots:
                exclude_slots[timestr] += 1
            else:
                exclude_slots[timestr] = 1
            service_start += ten_minutes

    while current_time <= end_time:
        time_str = current_time.strftime('%H:%M')
        if time_str not in exclude_slots or exclude_slots[time_str] < max_slots:
            time_slices.append(time_str)
        current_time += ten_minutes

    return time_slices


@background
def notify_user_when_checkout_ends(checkout_id):
    checkout = Checkout.objects.get(pk=checkout_id)
    SendMessage(checkout.user, "Через 10 минут закончим мыть ваш автомобиль!")