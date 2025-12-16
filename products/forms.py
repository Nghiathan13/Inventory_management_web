from django import forms
from decimal import Decimal, InvalidOperation


# --- Models ---
from .models import (
    Product, ProductCategory, UnitOfMeasure, UomCategory, BillOfMaterials
)

# =======================================================
#               DANH MỤC SẢN PHẨM
# =======================================================
class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ['name', 'parent', 'description']
        labels = {
            'name': 'Category Name',
            'parent': 'Parent Category',
            'description': 'Description',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g., Painkillers, Vitamins'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter category description...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['parent'].required = False
        self.fields['parent'].empty_label = "--------- (No Parent) ---------"
        self.fields['parent'].queryset = ProductCategory.objects.all().order_by('name')


# =======================================================
#               NHÓM ĐƠN VỊ TÍNH
# =======================================================
class UomCategoryForm(forms.ModelForm):
    class Meta:
        model = UomCategory
        fields = ['name', 'description']
        labels = {
            'name': 'UoM Category Name', 
            'description': 'Description'
        }
        widgets = {
           'name': forms.TextInput(attrs={'placeholder': 'e.g., Weight, Volume, Quantity'}),
           'description': forms.Textarea(attrs={'rows': 3}),
       }


# =======================================================
#               ĐƠN VỊ TÍNH (UoM)
# =======================================================
class UnitOfMeasureForm(forms.ModelForm):
    class Meta:
        model = UnitOfMeasure
        fields = ['name', 'category', 'uom_type', 'active', 'rounding_precision']
        labels = {
            'name': 'Unit Name',
            'category': 'Category',
            'uom_type': 'Type',
            'active': 'Active',
            'rounding_precision': 'Rounding Precision',
        }
        widgets = {
           'rounding_precision': forms.NumberInput(attrs={'step': 'any'})
       }


# =======================================================
#               QUY TẮC QUY ĐỔI (BOM)
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
            'conversion_factor': forms.NumberInput(attrs={'step': '1'}),
        }


# =======================================================
#               SẢN PHẨM (PRODUCT)
# =======================================================
class ProductForm(forms.ModelForm):
    import_price = forms.CharField(
        label="Cost Price", 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter cost...'})
    )
    sale_price = forms.CharField(
        label="Selling Price", 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter price...'})
    )
    quantity = forms.IntegerField(
        label="Total Quantity", 
        min_value=0, 
        required=True,
    )

    class Meta:
        model = Product
        fields = [
            'name', 'code', 'category', 'quantity',     
            'base_uom', 'uom_category', 
            'import_price', 'sale_price', 
            'reorder_point', 'supplier', 
            'description', 'image'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-control'})

    def _clean_price_field(self, field_name):
        price_str = self.cleaned_data.get(field_name)
        if not price_str: 
            return None
        
        clean_str = price_str.replace('.', '').replace(',', '').strip()
        try:
            return Decimal(clean_str)
        except (InvalidOperation, ValueError):
            raise forms.ValidationError("Invalid price format. Numbers only.")

    def clean_import_price(self):
        return self._clean_price_field('import_price')

    def clean_sale_price(self):
        return self._clean_price_field('sale_price')