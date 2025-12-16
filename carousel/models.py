from django.db import models
from products.models import Product, UnitOfMeasure, ProductBatch

# =======================================================
#               HỆ THỐNG KỆ XOAY
# =======================================================
class Carousel(models.Model):
    name = models.CharField(
        max_length=100, 
        default="Carousel System"
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
        status = "Moving" if self.is_moving else "Ready"
        return f"{self.name} (Gate: {self.current_shelf_at_gate}, Status: {status})"

# =======================================================
#               CỘT KỆ ĐƠN
# =======================================================
class Shelf(models.Model):
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
        return f"Shelf {self.name}"

# =======================================================
#               KHAY CHỨA (TẦNG)
# =======================================================
class Tray(models.Model):
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
        return f"Shelf {self.shelf.name}, Level {self.level}"

# =======================================================
#               VỊ TRÍ KHO & TỒN KHO
# =======================================================
class StockLocation(models.Model):
    tray = models.OneToOneField(
        Tray, 
        on_delete=models.CASCADE, 
        related_name='location'
    )
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='locations',
        verbose_name="Product"
    )
    batch = models.ForeignKey(
        ProductBatch, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='batch_locations',
        verbose_name="Batch"
    )
    quantity = models.PositiveIntegerField(
        default=0,
        verbose_name="Quantity"
    )
    quantity_uom = models.ForeignKey(
        UnitOfMeasure, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='stock_locations_qty',
        verbose_name="Unit (Qty)"
    )
    capacity = models.PositiveIntegerField(
        default=51,
        verbose_name="Max Capacity"
    )
    capacity_uom = models.ForeignKey(
        UnitOfMeasure, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='stock_locations_cap',
        verbose_name="Unit (Cap)"
    )
    
    class Meta:
        verbose_name = "Stock Location"
        verbose_name_plural = "Stock Locations"

    def __str__(self):
        batch_info = f" | Batch: {self.batch.batch_number}" if self.batch else ""
        return f"{self.product.name}{batch_info} @ {self.tray}"