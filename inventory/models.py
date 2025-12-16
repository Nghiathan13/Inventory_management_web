import uuid
from django.db import models
from django.contrib.auth.models import User

# =======================================================
#           GIAO DỊCH XUẤT (ORDER)
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
        return f'{product_name} - Qty: {self.order_quantity or "N/A"} by {staff_name}'

# =======================================================
#           ĐƠN ĐẶT HÀNG (PO)
# =======================================================
class PurchaseOrder(models.Model):
    STATUS_CHOICES = (
        ('To Confirm', 'Pending Supplier Confirmation'),
        ('Confirmed', 'Confirmed (Awaiting Delivery)'),
        ('Received', 'Received'),
        ('Cancelled', 'Cancelled'),
    )
    supplier = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        limit_choices_to={'groups__name': "Supplier"}, 
        verbose_name="Supplier"
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_purchase_orders', 
        verbose_name="Created By"
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
        verbose_name="Expiry Date (Supplier Input)"
    )

    class Meta:
        db_table = 'dashboard_purchaseorder'

    def __str__(self): 
        return f"PO #{self.id} - {self.supplier.username if self.supplier else 'N/A'}"

# =======================================================
#           CHI TIẾT ĐƠN HÀNG (PO DETAIL)
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
        verbose_name="Expiry Date (Supplier Input)"
    )
   
    class Meta:
        db_table = 'dashboard_purchaseorderdetail'

    def __str__(self): 
        return f"{self.product.name} - Qty: {self.quantity}"

# =======================================================
#           BIÊN LAI NHẬP KHO (RECEIPT)
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