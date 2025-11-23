from django import forms

# --- Models ---
from .models import Prescription, PrescriptionDetail
from patients.models import Patient
from products.models import UnitOfMeasure

# =======================================================
#               FORM QUẢN LÝ KÊ ĐƠN (PRESCRIPTION)
# =======================================================

class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['patient']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tải danh sách bệnh nhân và sắp xếp theo tên
        self.fields['patient'].queryset = Patient.objects.all().order_by('full_name')
        self.fields['patient'].empty_label = "--- Chọn Bệnh Nhân ---"

class PrescriptionDetailForm(forms.ModelForm):
    class Meta:
        model = PrescriptionDetail
        fields = ['product', 'uom', 'quantity']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'uom': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }