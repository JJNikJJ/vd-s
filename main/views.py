import json

from django.db import DatabaseError
from django.http import JsonResponse
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

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
        loyalty_data = loyalty_data.filter(service__in=Service.objects.filter(has_loyalty=True))
        serializer = UserDiscountsSerializer(loyalty_data, many=True)
        return JsonResponse(serializer.data, safe=False)


class UserCheckoutsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        checkouts = Checkout.objects.filter(user=user)
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

        services = ServicePrice.objects.filter(id__in=services_list)
        price_sum = 0
        approved = []
        finalServices = []
        for service in services:
            price = CarClassHasServicePrice.objects \
                .filter(carClass=car_class, servicePrice=service).first()
            if not price:
                continue
            price_sum += price.price
            approved.append(service)
            finalServices.append(price)

        if len(approved) == 0:
            return JsonResponse(
                {'message': 'Ошибка: выбранных услуг не существует для текущего класса автомобиля пользователя.'})

        checkout = Checkout.objects.create(
            user=request.user,
            address=Address.objects.get(id=address),
            target_datetime=datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S'),
            payment_type=PaymentType.objects.get(id=payment_type),
            final_price=price_sum,
        )

        try:
            checkout.services_list.set(list(map(lambda x: x.id, finalServices)))
            checkout.save()
        except DatabaseError as e:
            checkout.delete()
            return JsonResponse(
                {'message': f'Ошибка: {str(e)}'})

        # return JsonResponse({'message': 'OK'})
        return JsonResponse(data={'message': 'OK',
                                  'approved': list(map(lambda x: x.id, approved)),
                                  'finalServices': list(map(lambda x: x.id, finalServices))}, safe=False)


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
            return JsonResponse({'message': 'Ошибка: пользователь не найден данных сессии.'})

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
            car.mark = mark
            car.model = model
            car.number = car_number
        else:
            car = Car.objects.create(mark=mark, model=model, number=car_number)
            user.car = car

        car.save()
        user.save()

        return JsonResponse({'message': 'OK'})
