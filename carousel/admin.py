from django.contrib import admin
from .models import Carousel, Shelf, Tray, StockLocation

# =======================================================
#               CẤU HÌNH INLINE (HIỂN THỊ LỒNG NHAU)
# =======================================================

class TrayInline(admin.TabularInline):
    """
    Cho phép thêm/sửa/xóa Tầng (Tray) ngay trong trang chi tiết Kệ (Shelf).
    """
    model = Tray
    extra = 1  
    ordering = ('level',) 

class ShelfInline(admin.TabularInline):
    """
    Cho phép thêm/sửa/xóa Kệ (Shelf) ngay trong trang Carousel.
    """
    model = Shelf
    extra = 1
    ordering = ('name',)

# =======================================================
#               ĐĂNG KÝ CÁC MODEL VÀO ADMIN
# =======================================================

@admin.register(Carousel)
class CarouselAdmin(admin.ModelAdmin):
    list_display = ('name', 'current_shelf_at_gate', 'is_moving')
    inlines = [ShelfInline]

@admin.register(Shelf)
class ShelfAdmin(admin.ModelAdmin):
    list_display = ('name', 'carousel', 'count_trays')
    list_filter = ('carousel',)
    search_fields = ('name',)
    inlines = [TrayInline]

    def count_trays(self, obj):
        return obj.trays.count()
    count_trays.short_description = "Số lượng tầng"

@admin.register(Tray)
class TrayAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'shelf', 'level')
    list_filter = ('shelf__carousel', 'shelf')
    ordering = ('shelf', 'level')

@admin.register(StockLocation)
class StockLocationAdmin(admin.ModelAdmin):
    """
    Quản lý vị trí kho (Dành cho debug hoặc kiểm tra dữ liệu).
    """
    list_display = ('tray', 'product', 'batch', 'quantity', 'capacity')
    list_filter = ('product', 'batch')
    search_fields = ('product__name', 'tray__shelf__name')
    autocomplete_fields = ['product', 'batch']