from django import forms
from main.models import Checkout


class CheckoutAdminForm(forms.ModelForm):
    class Meta:
        model = Checkout

    def close_checkout_action(self):
        print("Order closed")
        pass