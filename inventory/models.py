# inventory/models.py

from django.db import models
from django.contrib.auth.models import User
import uuid

# =======================================================
#               MODEL GIAO DỊCH: ORDER
# =======================================================
class Order(models.Model):
    prescription = models.ForeignKey(
        'doctor.Prescription', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="From Prescription"
    )
    product = models.ForeignKey(
        'products.Product', 
        on_delete=models.CASCADE, 
        null=True
    )
    staff = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True
    )
    order_quantity = models.PositiveIntegerField(
        null=True, 
        blank=True
    )
    date = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = 'dashboard_order'
        verbose_name_plural = 'Orders'
        ordering = ['-date']

    def __str__(self):
        staff_name = self.staff.username if self.staff else "N/A"
        product_name = self.product.name if self.product else "Deleted Product"
        return f'{product_name} - SL: {self.order_quantity or "N/A"} bởi {staff_name}'

# =======================================================
#               MODEL ĐẶT HÀNG: PURCHASEORDER
# =======================================================
class PurchaseOrder(models.Model):
    STATUS_CHOICES = (
        ('To Confirm', 'Chờ Nhà Cung Cấp Xác Nhận'),
        ('Confirmed', 'Đã Xác Nhận (Chờ Giao)'),
        ('Received', 'Đã Nhận Hàng'),
        ('Cancelled', 'Đã Hủy'),
    )
    supplier = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        limit_choices_to={'groups__name': "Supplier"}, 
        verbose_name="Nhà Cung Cấp"
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_purchase_orders', 
        verbose_name="Người Tạo Đơn"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='To Confirm'
    )
    notes = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Notes"
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    confirmed_at = models.DateTimeField(
        null=True, 
        blank=True
    )
    received_at = models.DateTimeField(
        null=True, 
        blank=True
    )
    unique_code = models.UUIDField(
        default=uuid.uuid4, 
        editable=False, 
        unique=True
    )
    expiry_date = models.DateField(
        null=True, 
        blank=True, 
        verbose_name="Hạn Sử Dụng (Supplier nhập)"
    )

    class Meta:
        db_table = 'dashboard_purchaseorder'

    def __str__(self): 
        return f"PO #{self.id} - {self.supplier.username if self.supplier else 'N/A'}"

# =======================================================
#               MODEL CHI TIẾT: PURCHASEORDERDETAIL
# =======================================================
class PurchaseOrderDetail(models.Model):
    purchase_order = models.ForeignKey(
        PurchaseOrder, 
        on_delete=models.CASCADE, 
        related_name='details'
    )
    product = models.ForeignKey(
        'products.Product', 
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField()
    unique_code = models.UUIDField(
        default=uuid.uuid4, 
        editable=False, 
        unique=True
    ) 
    expiry_date = models.DateField(
        null=True, 
        blank=True, 
        verbose_name="Hạn Sử Dụng (Supplier nhập)"
    )
   
    class Meta:
        db_table = 'dashboard_purchaseorderdetail'

    def __str__(self): 
        return f"{self.product.name} - Qty: {self.quantity}"

# =======================================================
#               MODEL NHẬP KHO: STOCKRECEIPT
# =======================================================
class StockReceipt(models.Model):
    product = models.ForeignKey(
        'products.Product', 
        on_delete=models.CASCADE
    )
    quantity_received = models.PositiveIntegerField()
    expiry_date = models.DateField(
        null=True, 
        blank=True
    )
    received_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True
    )
    received_at = models.DateTimeField(
        auto_now_add=True
    )
    from_po_detail = models.OneToOneField(
        PurchaseOrderDetail, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )

    class Meta:
        db_table = 'dashboard_stockreceipt'

    def __str__(self):
        return f"Received {self.quantity_received} of {self.product.name} on {self.received_at.strftime('%d/%m/%Y')}"