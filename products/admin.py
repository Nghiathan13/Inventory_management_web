from django.contrib import admin
from .models import Product, ProductBatch, ProductCategory, UnitOfMeasure, UomCategory, BillOfMaterials

# =======================================================
#  BẮT BUỘC PHẢI CÓ SEARCH_FIELDS CHO PRODUCT & BATCH
#  để autocomplete_fields bên Carousel hoạt động
# =======================================================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'category', 'quantity', 'base_uom']
    list_filter = ['category', 'uom_category']
    # Dòng này QUAN TRỌNG để sửa lỗi E039:
    search_fields = ['name', 'code'] 

@admin.register(ProductBatch)
class ProductBatchAdmin(admin.ModelAdmin):
    list_display = ['batch_number', 'product', 'expiry_date', 'quantity']
    list_filter = ['expiry_date']
    # Dòng này QUAN TRỌNG để sửa lỗi E039:
    search_fields = ['batch_number', 'product__name'] 

# =======================================================
#           CÁC MODEL KHÁC
# =======================================================
@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent']
    search_fields = ['name']

@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'uom_type']
    list_filter = ['category']

@admin.register(UomCategory)
class UomCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(BillOfMaterials)
class BillOfMaterialsAdmin(admin.ModelAdmin):
    list_display = ['product', 'uom_from', 'uom_to', 'conversion_factor']