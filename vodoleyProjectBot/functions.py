import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vodoleyProject.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
import django
django.setup()
from main.models import CustomUser


def IsUserExist(username):
    try:
        user = CustomUser.objects.get(username=username)
        return True
    except CustomUser.DoesNotExist:
        return False
