from django import forms
from .models import Patient

# =======================================================
#               FORM QUẢN LÝ BỆNH NHÂN (PATIENT)
# =======================================================
class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        # Liệt kê tất cả các trường muốn hiển thị trong form
        fields = [
            'full_name', 'date_of_birth', 'gender', 'phone_number', 'address', 'avatar',
            'citizen_id', 'health_insurance_id', 'ethnicity', 'blood_type',
            'allergies', 'medical_history'
        ]
        
        # Thêm class 'form-control' của Bootstrap cho các widget
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'allergies': forms.Textarea(attrs={'rows': 3}),
            'medical_history': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Vòng lặp để tự động thêm class 'form-control' cho tất cả các trường
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-control'