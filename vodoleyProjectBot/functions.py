import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vodoleyProject.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
import django
django.setup()
from rest_framework.authtoken.models import Token
from main.models import CustomUser
from main.models import UserChat
from main.models import Checkout
from datetime import timedelta


def GetUser(username):
    try:
        try:
            user = CustomUser.objects.get(telegram=f"@{username}")
        except CustomUser.DoesNotExist:
            user = CustomUser.objects.get(telegram=username)
        return user
    except CustomUser.DoesNotExist:
        return None


def GetActiveCheckout(user):
    try:
        checkouts = Checkout.objects.filter(user=user, status=False, canceled=False).order_by('target_datetime')
        filtered = [x for x in checkouts if not x.is_past_due]
        if len(filtered) == 0:
            return None
        else:
            return filtered[0]
    except Checkout.DoesNotExist:
        return None


def GetToken(user):
    return Token.objects.get_or_create(user=user)


def PostponeOrder(checkout):
    if checkout.postponed:
        return
    date = checkout.target_datetime + timedelta(minutes=15)
    checkout.target_datetime = date
    checkout.postponed = True
    checkout.save()


def CancelOrder(checkout):
    checkout.canceled = True
    checkout.save()


def UpdateChatData(username, chatid):
    try:
        chat = UserChat.objects.get(telegram=username)
        chat.chat = chatid
        chat.save()
    except UserChat.DoesNotExist:
        try:
            chat = UserChat.objects.get(chat=chatid)
            chat.user = username
            chat.save()
        except UserChat.DoesNotExist:
            UserChat.objects.create(telegram=username, chat=chatid)