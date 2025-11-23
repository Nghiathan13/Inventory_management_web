from django import forms
from decimal import Decimal, InvalidOperation


# --- Models ---
from .models import (
    Product, ProductCategory, UnitOfMeasure, UomCategory, BillOfMaterials
)


# =======================================================
#               FORM QUẢN LÝ NHÓM SẢN PHẨM
# =======================================================
class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ['name', 'parent', 'description']
        labels = {
            'name': 'Tên Nhóm',
            'parent': 'Nhóm Cha',
            'description': 'Mô Tả',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g., Thuốc giảm đau, Vitamin'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Nhập mô tả cho nhóm sản phẩm'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Thiết lập các trường không bắt buộc và tùy chỉnh hiển thị
        self.fields['parent'].required = False
        self.fields['parent'].empty_label = "--------- (Không có nhóm cha) ---------"
        self.fields['parent'].queryset = ProductCategory.objects.all().order_by('name')

# =======================================================
#               FORM QUẢN LÝ NHÓM ĐƠN VỊ TÍNH
# =======================================================
class UomCategoryForm(forms.ModelForm):
    class Meta:
        model = UomCategory
        fields = ['name', 'description']
        labels = {'name': 'Tên Nhóm ĐVT', 'description': 'Mô Tả'}
        widgets = {
           'name': forms.TextInput(attrs={'placeholder': 'e.g., Số lượng, Trọng lượng, Thể tích'}),
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
            'name': 'Tên Đơn Vị Tính',
            'category': 'Thuộc Nhóm',
            'uom_type': 'Loại',
            'active': 'Hoạt động',
            'rounding_precision': 'Độ chính xác làm tròn',
        }
        widgets = {
           'rounding_precision': forms.NumberInput(attrs={'step': 'any'})
       }

# =======================================================
#               FORM QUẢN LÝ BẢNG QUY ĐỔI (BOM)
# =======================================================
class BillOfMaterialsForm(forms.ModelForm):
    class Meta:
        model = BillOfMaterials
        fields = ['product', 'uom_from', 'uom_to', 'conversion_factor']
        labels = {
            'product': 'Sản phẩm',
            'uom_from': 'Từ Đơn Vị',
            'uom_to': 'Sang Đơn Vị',
            'conversion_factor': 'Hệ Số Quy Đổi'
        }
        widgets = {
            'conversion_factor': forms.NumberInput(attrs={'step': '1'}),
        }

# =======================================================
#               FORM QUẢN LÝ SẢN PHẨM (PRODUCT)
# =======================================================
class ProductForm(forms.ModelForm):
    import_price = forms.CharField(
        label="Giá Nhập", 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập giá...'})
    )
    sale_price = forms.CharField(
        label="Giá Bán", 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập giá...'})
    )
    quantity = forms.IntegerField(
        label="Tổng Số Lượng Tồn Kho", 
        min_value=0, 
        required=True,
    )

    class Meta:
        model = Product
        fields = [
            'name', 
            'code', 
            'category', 
            'quantity',     
            'base_uom', 
            'uom_category', 
            'import_price', 
            'sale_price', 
            'reorder_point', 
            'supplier', 
            'description', 
            'image'
        ]

        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        # Style cho đẹp (Bootstrap)
        for field in self.fields:
            # Kiểm tra field widget type để không ghi đè checkbox/file input nếu không cần thiết
            if not isinstance(self.fields[field].widget, (forms.CheckboxInput, forms.FileInput)):
                self.fields[field].widget.attrs.update({'class': 'form-control'})
            elif isinstance(self.fields[field].widget, forms.FileInput):
                self.fields[field].widget.attrs.update({'class': 'form-control'})

    # Validate giá bán không được nhỏ hơn giá nhập (nếu muốn)
    def clean(self):
        cleaned_data = super().clean()
        import_price = cleaned_data.get("import_price")
        sale_price = cleaned_data.get("sale_price")

        if import_price and sale_price and sale_price < import_price:
             # Có thể cảnh báo hoặc raise error tùy logic
             pass 
        return cleaned_data

    # Hàm xử lý làm sạch dữ liệu cho giá nhập
    def clean_import_price(self):
        price_str = self.cleaned_data.get('import_price')
        if not price_str: return None
        cleaned_price_str = price_str.replace('.', '').replace(',', '').strip()
        try:
            return Decimal(cleaned_price_str)
        except (InvalidOperation, ValueError):
            raise forms.ValidationError("Giá nhập không hợp lệ. Vui lòng chỉ nhập số.")

    # Hàm xử lý làm sạch dữ liệu cho giá bán
    def clean_sale_price(self):
        price_str = self.cleaned_data.get('sale_price')
        if not price_str: return None
        cleaned_price_str = price_str.replace('.', '').replace(',', '').strip()
        try:
            return Decimal(cleaned_price_str)
        except (InvalidOperation, ValueError):
            raise forms.ValidationError("Giá bán không hợp lệ. Vui lòng chỉ nhập số.")