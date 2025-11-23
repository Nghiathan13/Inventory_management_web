from django.db import models
from products.models import Product, UnitOfMeasure, ProductBatch

# =======================================================
#               MODEL: CAROUSEL
# =======================================================
class Carousel(models.Model):
    """Đại diện cho toàn bộ hệ thống kệ xoay."""
    name = models.CharField(
        max_length=100, 
        default="Hệ Thống Kệ Xoay"
    )
    current_shelf_at_gate = models.CharField(
        max_length=1, 
        default='A'
    )
    target_shelf = models.CharField(
        max_length=1, 
        null=True, 
        blank=True
    )
    is_moving = models.BooleanField(
        default=False
    )

    def __str__(self):
        status = "Di chuyển" if self.is_moving else "Sẵn sàng"
        return f"{self.name} (Tại cửa: {self.current_shelf_at_gate}, Trạng thái: {status})"

# =======================================================
#               MODEL: SHELF
# =======================================================
class Shelf(models.Model):
    """Đại diện cho một cột kệ đơn (ví dụ: Kệ A, Kệ B)."""
    carousel = models.ForeignKey(
        Carousel, 
        on_delete=models.CASCADE, 
        related_name='shelves'
    )
    name = models.CharField(
        max_length=1, 
        unique=True
    )
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Shelves'

    def __str__(self):
        return f"Kệ {self.name}"

# =======================================================
#               MODEL: TRAY
# =======================================================
class Tray(models.Model):
    """Đại diện cho một khay (tầng) trên một kệ cụ thể."""
    shelf = models.ForeignKey(
        Shelf, 
        on_delete=models.CASCADE, 
        related_name='trays'
    )
    level = models.PositiveIntegerField()
    
    class Meta:
        unique_together = ('shelf', 'level')
        ordering = ['shelf__name', 'level']

    def __str__(self):
        return f"Kệ {self.shelf.name}, Tầng {self.level}"


# =======================================================
#               MODEL: STOCK LOCATION
# =======================================================
class StockLocation(models.Model):
    """Model trung gian, gán một Sản phẩm vào một Khay và định nghĩa sức chứa."""
    tray = models.OneToOneField(
        Tray, 
        on_delete=models.CASCADE, 
        related_name='location'
    )
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='locations',
        verbose_name="Sản Phẩm"
    )
    batch = models.ForeignKey(
        ProductBatch, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='batch_locations',
        verbose_name="Lô Hàng"
    )
    quantity = models.PositiveIntegerField(
        default=0,
        verbose_name="Số Lượng"
    )
    quantity_uom = models.ForeignKey(
        UnitOfMeasure, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='stock_locations_qty',
        verbose_name="Đơn Vị (SL)"
    )
    capacity = models.PositiveIntegerField(
        default=51,
        verbose_name="Sức Chứa Max"
    )
    capacity_uom = models.ForeignKey(
        UnitOfMeasure, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='stock_locations_cap',
        verbose_name="Đơn Vị (Max)"
    )
    
    class Meta:
        verbose_name = "Vị Trí Kho"
        verbose_name_plural = "Vị Trí Kho"


    def __str__(self):
        product_name = self.product.name if self.product else "Sản phẩm trống"
        batch_info = f" | Lô: {self.batch.batch_number}" if self.batch else ""
        return f"{self.product.name}{batch_info} @ {self.tray}"