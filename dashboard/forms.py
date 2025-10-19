# =======================================================
#               KHAI BÁO THƯ VIỆN (IMPORTS)
# =======================================================
from django import forms
from .models import (
    Product, Order, Prescription,
    PrescriptionDetail, Patient, ProductCategory,
    UnitOfMeasure, UomCategory, BillOfMaterials
)
from decimal import Decimal, InvalidOperation


# =======================================================
#               FORM QUẢN LÝ NHÓM ĐƠN VỊ TÍNH
# =======================================================
class UomCategoryForm(forms.ModelForm):
    class Meta:
        model = UomCategory
        fields = ['name', 'description']
        labels = {'name': 'Category Name', 'description': 'Description'}
        widgets = {
           'name': forms.TextInput(attrs={'placeholder': 'e.g., Count, Weight, Volume'}),
           'description': forms.Textarea(attrs={'rows': 3}),
       }

# =======================================================
#               FORM QUẢN LÝ ĐƠN VỊ TÍNH (UoM)
# =======================================================
class UnitOfMeasureForm(forms.ModelForm):
    class Meta:
        model = UnitOfMeasure
        fields = ['name', 'category', 'uom_type', 'active', 'rounding_precision']
        labels = {
            'name': 'Unit of Measure',
            'category': 'Category',
            'uom_type': 'Type',
            'active': 'Active',
            'rounding_precision': 'Rounding Precision',
        }
        widgets = {
           'rounding_precision': forms.NumberInput(attrs={'step': 'any'})
       }

# =======================================================
#               FORM QUẢN LÝ BOM form
# =======================================================
class BillOfMaterialsForm(forms.ModelForm):
    class Meta:
        model = BillOfMaterials
        fields = ['product', 'uom_from', 'uom_to', 'conversion_factor']
        labels = {
            'product': 'Product',
            'uom_from': 'From Unit',
            'uom_to': 'To Unit',
            'conversion_factor': 'Conversion Factor'
        }
        widgets = {
            'conversion_factor': forms.NumberInput(attrs={'step': 'any'}),
        }

# =======================================================
#               FORM QUẢN LÝ SẢN PHẨM (PRODUCT)
# =======================================================
class ProductForm(forms.ModelForm):
    import_price = forms.CharField(
        label="Import Price",
        required=False, 
    )
    sale_price = forms.CharField(
        label="Sale Price",
        required=False, 
    )
    category = forms.ModelChoiceField(
        queryset=ProductCategory.objects.all(),
        required=False,
        label="Nhóm sản phẩm"
    )

    class Meta:
        model = Product
        fields = [
            'name', 'code', 'category', 'uom', 'quantity',
            'import_price', 'sale_price', 'expiry_date', 'supplier',
            'description'
        ]

        labels = {
            'name': 'Product Name',
            'code': 'Product Code',
            'category': 'Product Category', 
            'uom': 'Base UoM',
            'quantity': 'Quantity',
            'expiry_date': 'Expiry Date',
            'supplier': 'Supplier',
            'description': 'Description',
        }

        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter product name'}),
            'code': forms.TextInput(attrs={'placeholder': 'Enter product code'}),
            'supplier': forms.TextInput(attrs={'placeholder': 'Enter supplier name'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'import_price': forms.TextInput(attrs={'placeholder': 'e.g., 1,200,000'}),
            'sale_price': forms.TextInput(attrs={'placeholder': 'e.g., 1,500,000'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_import_price(self):
        price_str = self.cleaned_data.get('import_price')
        if not price_str:
            return None 
        cleaned_price_str = price_str.replace('.', '').replace('.', '').strip()
        try:
            return Decimal(cleaned_price_str)
        except (InvalidOperation, ValueError):
            raise forms.ValidationError("Invalid import price. Please enter numbers only.")

    def clean_sale_price(self):
        price_str = self.cleaned_data.get('sale_price')
        if not price_str:
            return None
            
        cleaned_price_str = price_str.replace('.', '').replace('.', '').strip()
        try:
            return Decimal(cleaned_price_str)
        except (InvalidOperation, ValueError):
            raise forms.ValidationError("Invalid sale price. Please enter numbers only.")


# =======================================================
#               FORM QUẢN LÝ NHÓM SẢN PHẨM
#   Xử lý việc thêm và cập nhật các nhóm/danh mục sản phẩm.
# =======================================================
class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        
        # Các trường sẽ hiển thị trong form
        fields = ['name', 'parent', 'description']
        
        # Tùy chỉnh nhãn (label) cho các trường
        labels = {
            'name': 'Category Name',
            'parent': 'Parent Category',
            'description': 'Description',
        }
        
        # Thêm placeholder và các thuộc tính khác cho widget
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g., Painkillers, Vitamins'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter a description for the category'}),
        }

    def __init__(self, *args, **kwargs):
        """
        Ghi đè hàm khởi tạo để tùy chỉnh thêm cho trường 'parent'.
        """
        super().__init__(*args, **kwargs)
        
        # Làm cho trường 'parent' không bắt buộc (optional)
        self.fields['parent'].required = False
        
        # Thêm một lựa chọn "rỗng" vào đầu danh sách Parent Category
        self.fields['parent'].empty_label = "--------- (No Parent Category) ---------"
        
        # Sắp xếp danh sách các danh mục cha theo tên cho dễ tìm
        self.fields['parent'].queryset = ProductCategory.objects.all().order_by('name')



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
    uom = forms.ModelChoiceField(
        queryset=UnitOfMeasure.objects.all(),
        label="Đơn vị",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = PrescriptionDetail
        fields = ['product', 'uom', 'quantity']
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