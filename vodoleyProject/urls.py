from django.contrib import admin
from django.urls import path
from main.views import *


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth-obtain-token/', AuthObtainToken.as_view(), name='auth-obtain-token'),
    path('api/auth-register/', RegisterUser, name='auth-register'),
    path('api/auth-login/', LoginUser, name='auth-login'),
    path('api/edit-user/', EditUser.as_view(), name='edit-user'),
    path('api/get-main-page/', MainPage.as_view(), name='get-main-page'),
    path('api/get-addresses-list/', AddressListView.as_view(), name='get-addresses-list'),
    path('api/get-services-for-address/', GetServicesForAddress.as_view(), name='get-services-for-address'),
    path('api/get-user-checkouts/', UserCheckoutsView.as_view(), name='get-user-checkouts'),
    path('api/create-checkout/', CreateCheckout.as_view(), name='create-checkout'),
    path('api/postpone-checkout/', PostponeCheckout.as_view(), name='postpone-checkout'),
    path('api/get-user-discounts/', UserDiscountsView.as_view(), name='get-user-discounts'),
    path('api/get-payment-methods/', PaymentTypeListView.as_view(), name='get-payment-methods'),
    path('api/edit-checkout/', EditCheckout.as_view(), name='edit-checkout'),
    path('api/cancel-checkout/', CancelCheckout.as_view(), name='cancel-checkout'),

]
