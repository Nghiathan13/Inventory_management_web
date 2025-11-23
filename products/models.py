from django.db import models
from django.db.models import Sum
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

# =======================================================
#               CÁC HẰNG SỐ LỰA CHỌN (CHOICES)
# =======================================================
UOM_TYPE_CHOICES = (
    ('reference', 'Reference Unit for this category'),
    ('bigger', 'Bigger than the reference Unit of Measure'),
    ('smaller', 'Smaller than the reference Unit of Measure'),
)

# =======================================================
#               MODEL: UNITOFMEASURE (UoM)
# =======================================================
class UomCategory(models.Model):
    name = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name="Category Name"
        )
    description = models.TextField(
        null=True, 
        blank=True, 
        verbose_name="Description"
    )

    class Meta:
        db_table = 'dashboard_uomcategory'
        verbose_name_plural = 'UoM Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


# =======================================================
#      MODEL: UNIT OF MEASURE CATEGORY (UOM CATEGORY)
# =======================================================
class UnitOfMeasure(models.Model):
    name = models.CharField(
        max_length=100, 
        verbose_name="Unit of Measure"
    )
    category = models.ForeignKey(
        UomCategory, 
        on_delete=models.CASCADE, 
        related_name='uoms', 
        verbose_name="Category"
    )
    uom_type = models.CharField(
        max_length=20, 
        choices=UOM_TYPE_CHOICES, 
        verbose_name="Type"
    )
    active = models.BooleanField(
        default=True, 
        verbose_name="Active"
    )
    rounding_precision = models.FloatField(
        default=0.01, 
        verbose_name="Rounding Precision")
    
    class Meta:
        db_table = 'dashboard_unitofmeasure'
        verbose_name_plural = 'Units of Measure'
        ordering = ['category', 'name']

    def __str__(self):
        return self.name

# =======================================================
#               MODEL: PRODUCTCATEGORY
# =======================================================
class ProductCategory(models.Model):
    name = models.CharField(
        max_length=100, 
        verbose_name="Category Name"
    )
    parent = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='children', 
        verbose_name="Parent Category"
    )
    description = models.TextField(null=True, blank=True, verbose_name="Description")

    class Meta:
        db_table = 'dashboard_productcategory'
        verbose_name_plural = 'Product Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

# =======================================================
#               MODEL: PRODUCT
# =======================================================
class Product(models.Model):
    code = models.CharField(
        max_length=50, 
        unique=True, 
        null=True, 
        verbose_name="Product Code"
    )
    name = models.CharField(
        max_length=100, 
        null=True, 
        verbose_name="Product Name"
    )
    quantity = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        verbose_name="Tổng Tồn Kho"
    )
    category = models.ForeignKey(
        ProductCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Category"
    )
    uom_category = models.ForeignKey(
        UomCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        verbose_name="UoM Category"
    )
    base_uom = models.ForeignKey(
        UnitOfMeasure, 
        on_delete=models.SET_NULL, 
        null=True, 
        verbose_name="Base Unit of Measure"
    )
    import_price = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        verbose_name="Import Price"
    )
    sale_price = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        verbose_name="Sale Price"
    )
    reorder_point = models.PositiveIntegerField(
        default=10, 
        verbose_name="Reorder Point"
    )
    supplier = models.CharField(
        max_length=100, 
        null=True, 
        blank=True, 
        verbose_name="Default Supplier"
    )
    description = models.TextField(
        null=True, 
        blank=True, 
        verbose_name="Description"
    )
    image = models.ImageField(
        upload_to='product_images/', 
        null=True, 
        blank=True, 
        verbose_name="Product Image"
    )

    @property
    def total_quantity(self):
        """Tổng số lượng của tất cả các lô cộng lại."""
        return self.batches.aggregate(total=Sum('quantity'))['total'] or 0
    
    @property
    def allocated_quantity(self):
        """Tính tổng số lượng đã phân bổ lên kệ."""
        total_base_quantity = 0
        for batch in self.batches.all():
            # SỬA LẠI: Dùng batch_locations cho đúng related_name
            for loc in batch.batch_locations.all():
                if loc.quantity > 0:
                    # Logic quy đổi BOM
                    if loc.quantity_uom and loc.quantity_uom_id != self.base_uom_id:
                        bom_rule = self.boms.filter(
                            uom_from_id=loc.quantity_uom_id, 
                            uom_to_id=self.base_uom_id
                        ).first()
                        if bom_rule:
                            total_base_quantity += loc.quantity * bom_rule.conversion_factor
                        else:
                            total_base_quantity += loc.quantity
                    else:
                        total_base_quantity += loc.quantity
        return total_base_quantity

    @property
    def unallocated_quantity(self):
        """Tính số lượng chưa phân bổ."""
        return self.quantity - self.allocated_quantity
    
    class Meta:
        db_table = 'dashboard_product'
        verbose_name_plural = 'Products'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.code})'
    
# =======================================================
#               MODEL: PRODUCT BATCH (LÔ SẢN PHẨM)
# =======================================================
class ProductBatch(models.Model):
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='batches', 
        verbose_name="Sản Phẩm"
    )
    batch_number = models.CharField(
        max_length=50, 
        verbose_name="Mã Lô"
    )
    expiry_date = models.DateField(
        verbose_name="Hạn Sử Dụng"
    )
    quantity = models.PositiveIntegerField(
        default=0, 
        verbose_name="Số Lượng"
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = 'products_batch'
        ordering = ['expiry_date']

    def __str__(self):
        return f"{self.product.name} - Lô: {self.batch_number}"
    

# =======================================================
#               MODEL: BILLOFMATERIALS (BOM)
# =======================================================
class BillOfMaterials(models.Model):
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='boms', 
        verbose_name="Product"
    )
    uom_from = models.ForeignKey(
        UnitOfMeasure, 
        on_delete=models.CASCADE, 
        related_name='boms_from', 
        verbose_name="From Unit"
    )
    uom_to = models.ForeignKey(
        UnitOfMeasure, 
        on_delete=models.CASCADE, 
        related_name='boms_to', 
        verbose_name="To Unit"
    )
    conversion_factor = models.IntegerField(
        verbose_name="Conversion Factor"
    )

    class Meta:
        db_table = 'dashboard_billofmaterials'
        verbose_name_plural = 'Bills of Materials'
        unique_together = ('product', 'uom_from', 'uom_to')

    def __str__(self):
        return f"{self.product.name}: 1 {self.uom_from.name} = {self.conversion_factor} {self.uom_to.name}"

    def clean(self):
        if self.conversion_factor <= 0:
            raise ValidationError({'conversion_factor': 'Conversion factor must be a positive number.'})
        

# =======================================================
#               SIGNALS (TỰ ĐỘNG CẬP NHẬT TỒN KHO)
# =======================================================
@receiver(post_save, sender=ProductBatch)
@receiver(post_delete, sender=ProductBatch)
def update_product_total_stock(sender, instance, **kwargs):
    """
    Bất cứ khi nào Lô (Batch) được tạo, sửa, hoặc xóa:
    Hàm này sẽ tính tổng quantity của tất cả các lô thuộc sản phẩm đó
    và cập nhật vào trường Product.quantity.
    """
    product = instance.product
    # Tính tổng
    total = product.batches.aggregate(total=Sum('quantity'))['total'] or 0
    # Cập nhật và lưu (chỉ update trường quantity để tối ưu)
    product.quantity = total
    product.save(update_fields=['quantity'])