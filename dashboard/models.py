from django.db import models
from django.contrib.auth.models import User
from datetime import date

# =======================================================
#               CÁC HẰNG SỐ LỰA CHỌN (CHOICES)
#   Được định nghĩa ở đầu file để dễ dàng quản lý và tái sử dụng.
# =======================================================
GENDER_CHOICES = (
    ('Nam', 'Nam'),
    ('Nữ', 'Nữ'),
    ('Khác', 'Khác'),
)

PRESCRIPTION_STATUS_CHOICES = (
    ('Pending', 'Chờ lấy thuốc'),
    ('Dispensed', 'Đã lấy thuốc'),
    ('Cancelled', 'Đã hủy'),
)

BLOOD_TYPE_CHOICES = (
    ('A+', 'A+'), ('A-', 'A-'),
    ('B+', 'B+'), ('B-', 'B-'),
    ('AB+', 'AB+'), ('AB-', 'AB-'),
    ('O+', 'O+'), ('O-', 'O-'),
    ('Unknown', 'Chưa rõ'),
)


# =======================================================
#               CÁC MODEL KHÔNG PHỤ THUỘC
#   Các model này không phụ thuộc vào các model khác trong file này.
#   Chúng phải được định nghĩa trước.
# =======================================================

# =======================================================
#               MODEL: UNITOFMEASURE (UoM)
#   Lưu trữ các đơn vị tính (Viên, Vỉ, Hộp...).
# =======================================================
class UnitOfMeasure(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Unit Name")

    class Meta:
        verbose_name_plural = 'Units of Measure'
        ordering = ['name']

    def __str__(self):
        return self.name

# =======================================================
#               MODEL: PRODUCTCATEGORY
#   Lưu trữ thông tin về các nhóm/danh mục sản phẩm.
# =======================================================
class ProductCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name="Category Name")
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, 
        related_name='children', verbose_name="Parent Category")

    class Meta:
        verbose_name_plural = 'Product Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

# =======================================================
#               MODEL CƠ SỞ: PATIENT
#   Lưu trữ thông tin hồ sơ của từng bệnh nhân.
# =======================================================
class Patient(models.Model):
    full_name = models.CharField(max_length=255, verbose_name="Full Name")
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="Date of Birth")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, verbose_name="Gender")
    address = models.CharField(max_length=255, null=True, blank=True, verbose_name="Address")
    phone_number = models.CharField(max_length=15, null=True, blank=True, verbose_name="Phone Number")
    avatar = models.ImageField(upload_to='patient_avatars/', null=True, blank=True, verbose_name="Avatar")
    citizen_id = models.CharField(max_length=20, null=True, blank=True, unique=True, verbose_name="Citizen ID")
    health_insurance_id = models.CharField(max_length=20, null=True, blank=True, verbose_name="Health Insurance ID")
    ethnicity = models.CharField(max_length=50, null=True, blank=True, verbose_name="Ethnicity")
    blood_type = models.CharField(max_length=10, choices=BLOOD_TYPE_CHOICES, default='Unknown', verbose_name="Blood Type")
    allergies = models.TextField(null=True, blank=True, verbose_name="Allergies")
    medical_history = models.TextField(null=True, blank=True, verbose_name="Medical History")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Patients'
        ordering = ['-created_at']

    def __str__(self):
        return self.full_name

    @property
    def age(self):
        # Hàm tiện ích để tính tuổi từ ngày sinh
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None


# =======================================================
#               CÁC MODEL PHỤ THUỘC
#   Các model này có quan hệ ForeignKey đến các model ở trên.
# =======================================================

# =======================================================
#               MODEL CƠ SỞ: PRODUCT
#   Đại diện cho một loại thuốc hoặc sản phẩm y tế trong kho.
#   Phụ thuộc vào: ProductCategory, UnitOfMeasure.
# =======================================================
class Product(models.Model):
    code = models.CharField(max_length=50, unique=True, null=True, verbose_name="Product Code")
    name = models.CharField(max_length=100, null=True, verbose_name="Product Name")
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Category")
    quantity = models.PositiveIntegerField(null=True, verbose_name="Quantity")
    uom = models.ForeignKey(UnitOfMeasure, on_delete=models.SET_NULL, null=True, verbose_name="Base Unit of Measure")
    import_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, verbose_name="Import Price")
    sale_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, verbose_name="Sale Price")
    expiry_date = models.DateField(null=True, blank=True, verbose_name="Expiry Date")
    supplier = models.CharField(max_length=100, null=True, blank=True, verbose_name="Supplier")

    class Meta:
        verbose_name_plural = 'Products'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.code})'

# =======================================================
#               MODEL MỚI: BILLOFMATERIALS (BOM)
#   Định nghĩa cách quy đổi giữa các đơn vị.
#   Phụ thuộc vào: Product, UnitOfMeasure.
# =======================================================
class BillOfMaterials(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='boms', verbose_name="Product")
    uom_from = models.ForeignKey(UnitOfMeasure, on_delete=models.CASCADE, related_name='boms_from', verbose_name="From Unit")
    uom_to = models.ForeignKey(UnitOfMeasure, on_delete=models.CASCADE, related_name='boms_to', verbose_name="To Unit (Base)")
    conversion_factor = models.IntegerField(verbose_name="Conversion Factor")

    class Meta:
        verbose_name_plural = 'Bills of Materials'
        unique_together = ('product', 'uom_from')

    def __str__(self):
        return f"{self.product.name}: 1 {self.uom_from.name} = {self.conversion_factor} {self.uom_to.name}"

# =======================================================
#               MODEL GIAO DỊCH: PRESCRIPTION
#   Đại diện cho một toa thuốc tổng thể do bác sĩ kê cho bệnh nhân.
#   Phụ thuộc vào: Patient, User.
# =======================================================
class Prescription(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, verbose_name="Patient")
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, null=True, verbose_name="Doctor")
    status = models.CharField(max_length=20, choices=PRESCRIPTION_STATUS_CHOICES, default='Pending', verbose_name="Status")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Completed At")

    class Meta:
        verbose_name_plural = 'Prescriptions'
        ordering = ['-created_at']

    def __str__(self):
        patient_name = self.patient.full_name if self.patient else "Unknown"
        return f'Toa thuốc ID: #{self.id} - Bệnh nhân: {patient_name}'

# =======================================================
#               MODEL GIAO DỊCH: ORDER
#   Ghi lại một giao dịch xuất kho (bán hàng).
#   Phụ thuộc vào: Prescription, Product, User.
# =======================================================
class Order(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="From Prescription")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    staff = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    order_quantity = models.PositiveIntegerField(null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Orders'
        ordering = ['-date']

    def __str__(self):
        staff_name = self.staff.username if self.staff else "N/A"
        product_name = self.product.name if self.product else "Deleted Product"
        return f'{product_name} - SL: {self.order_quantity or "N/A"} bởi {staff_name}'

# =======================================================
#               MODEL CHI TIẾT: PRESCRIPTIONDETAIL
#   Lưu trữ chi tiết từng loại thuốc trong một toa thuốc.
#   Phụ thuộc vào: Prescription, Product, UnitOfMeasure.
# =======================================================
class PrescriptionDetail(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='details', verbose_name="Prescription")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, verbose_name="Product")
    quantity = models.PositiveIntegerField(null=True, verbose_name="Quantity")
    uom = models.ForeignKey(UnitOfMeasure, on_delete=models.SET_NULL, null=True, verbose_name="Unit")
    is_collected = models.BooleanField(default=False, verbose_name="Collected")

    class Meta:
        verbose_name_plural = 'Prescription Details'

    def __str__(self):
        product_name = self.product.name if self.product else "Deleted Product"
        return f'{product_name} - {self.quantity} (Toa: #{self.prescription.id})'