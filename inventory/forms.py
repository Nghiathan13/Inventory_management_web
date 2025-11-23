from django import forms
from .models import Order

# =======================================================
#               FORM QUẢN LÝ ĐƠN HÀNG (ORDER)
# =======================================================
class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['product', 'order_quantity']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'order_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }