# =======================================================
#               KHAI BÁO THƯ VIỆN (IMPORTS)
# =======================================================
from django import forms
from .models import (
    Product, Order, Prescription,
    PrescriptionDetail, Patient
)
from decimal import Decimal, InvalidOperation




# =======================================================
#               FORM QUẢN LÝ SẢN PHẨM (PRODUCT)
#   Xử lý việc thêm và cập nhật thông tin sản phẩm.
#   Bao gồm logic tùy chỉnh để xử lý giá tiền có dấu chấm.
# =======================================================
class ProductForm(forms.ModelForm):
    import_price = forms.CharField(
        label="Giá nhập",
        required=False, 
        widget=forms.TextInput(attrs={'placeholder': 'Ví dụ: 1.200.000', 'class': 'form-control'})
    )
    sale_price = forms.CharField(
        label="Giá bán",
        required=False, 
        widget=forms.TextInput(attrs={'placeholder': 'Ví dụ: 1.500.000', 'class': 'form-control'})
    )

    class Meta:
        model = Product
        fields = [
            'code', 'name', 'category', 'quantity', 'unit',
            'import_price', 'sale_price', 'expiry_date', 'supplier'
        ]
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def clean_import_price(self):
        """
        Làm sạch và chuyển đổi giá nhập từ chuỗi thành số Decimal.
        """
        price_str = self.cleaned_data.get('import_price')
        if not price_str:
            return None 
        cleaned_price_str = price_str.replace('.', '').strip()
        try:
            return Decimal(cleaned_price_str)
        except (InvalidOperation, ValueError):
            raise forms.ValidationError("Giá nhập không hợp lệ. Vui lòng chỉ nhập số.")

    def clean_sale_price(self):
        """
        Làm sạch và chuyển đổi giá bán từ chuỗi thành số Decimal.
        """
        price_str = self.cleaned_data.get('sale_price')
        if not price_str:
            return None
            
        cleaned_price_str = price_str.replace('.', '').strip()
        try:
            return Decimal(cleaned_price_str)
        except (InvalidOperation, ValueError):
            raise forms.ValidationError("Giá bán không hợp lệ. Vui lòng chỉ nhập số.")





# =======================================================
#               FORM QUẢN LÝ BỆNH NHÂN (PATIENT)
#   Xử lý việc thêm và cập nhật hồ sơ bệnh nhân.
# =======================================================
class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['full_name', 'date_of_birth', 'gender', 'phone_number', 'address', 'avatar',
            'citizen_id', 'health_insurance_id', 'ethnicity', 'blood_type',
            'allergies', 'medical_history']
        
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'blood_type': forms.Select(attrs={'class': 'form-control'}),
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'medical_history': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }





# =======================================================
#               FORM QUẢN LÝ KÊ ĐƠN (PRESCRIPTION)
#   Các form liên quan đến quy trình kê đơn thuốc của bác sĩ.
# =======================================================

# -------------------------------------------------------
#   FORM CHÍNH: Lấy thông tin bệnh nhân cho toa thuốc.
# -------------------------------------------------------
class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['patient']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['patient'].queryset = Patient.objects.all().order_by('full_name')


# -------------------------------------------------------
#   FORM CHI TIẾT: Lấy thông tin từng loại thuốc trong toa.
# -------------------------------------------------------
class PrescriptionDetailForm(forms.ModelForm):
    class Meta:
        model = PrescriptionDetail
        fields = ['product', 'quantity']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }





# =======================================================
#               FORM QUẢN LÝ ĐƠN HÀNG (ORDER)
#   Dành cho việc tạo đơn hàng/xuất kho thủ công (nếu có).
# =======================================================
class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['product', 'order_quantity']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'order_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }