from django.db import models
from django.contrib.auth.models import User

# =======================================================
#               CÁC HẰNG SỐ LỰA CHỌN (CHOICES)
#   Được định nghĩa ở đầu file để dễ dàng quản lý và tái sử dụng.
# =======================================================
CATEGORY = (
    ('Thuốc kê đơn', 'Thuốc kê đơn'),
    ('Thuốc không kê đơn', 'Thuốc không kê đơn'),
    ('Thực phẩm chức năng', 'Thực phẩm chức năng'),
    ('Dụng cụ y tế', 'Dụng cụ y tế'),
)

UNIT = (
    ('Viên', 'Viên'),
    ('Hộp', 'Hộp'),
    ('Chai', 'Chai'),
    ('Ống', 'Ống'),
    ('Gói', 'Gói'),
)

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
#               MODEL CƠ SỞ: PATIENT
#   Lưu trữ thông tin hồ sơ của từng bệnh nhân.
# =======================================================
class Patient(models.Model):
    # --- THÔNG TIN CÁ NHÂN ---
    full_name = models.CharField(
        max_length=255, verbose_name="Họ và tên")
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="Ngày sinh")
    gender = models.CharField(
        max_length=10, choices=GENDER_CHOICES, verbose_name="Giới tính")
    address = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Địa chỉ/Quê quán")
    phone_number = models.CharField(
        max_length=15, null=True, blank=True, verbose_name="Số điện thoại")
    
     # THÊM TRƯỜNG ẢNH ĐẠI DIỆN
    avatar = models.ImageField(upload_to='patient_avatars/', null=True, blank=True, verbose_name="Ảnh đại diện")

    # --- THÔNG TIN ĐỊNH DANH & BẢO HIỂM ---
    citizen_id = models.CharField(
        max_length=20, null=True, blank=True, unique=True, verbose_name="Số CCCD")
    health_insurance_id = models.CharField(
        max_length=20, null=True, blank=True, verbose_name="Số BHYT")
    ethnicity = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="Dân tộc")

    # --- THÔNG TIN Y TẾ ---
    blood_type = models.CharField(
        max_length=10, choices=BLOOD_TYPE_CHOICES, default='Unknown', verbose_name="Nhóm máu")
    allergies = models.TextField(null=True, blank=True, verbose_name="Tiền sử dị ứng")
    medical_history = models.TextField(null=True, blank=True, verbose_name="Bệnh sử (bệnh mãn tính)")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Patient'
        ordering = ['-created_at']

    def __str__(self):
        return self.full_name


     # Hàm tiện ích để tính tuổi từ ngày sinh
    @property
    def age(self):
        from datetime import date
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None
# =======================================================
#               MODEL CƠ SỞ: PRODUCT
#   Đại diện cho một loại thuốc hoặc sản phẩm y tế trong kho.
# =======================================================
class Product(models.Model):
    code = models.CharField(
        max_length=50, unique=True, null=True, verbose_name="Mã thuốc")
    name = models.CharField(max_length=100, null=True, verbose_name="Tên thuốc")
    category = models.CharField(
        max_length=50, choices=CATEGORY, null=True, verbose_name="Danh mục")
    quantity = models.PositiveIntegerField(null=True, verbose_name="Số lượng")
    unit = models.CharField(
        max_length=20, choices=UNIT, null=True, verbose_name="Đơn vị")
    import_price = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, verbose_name="Giá nhập")
    sale_price = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, verbose_name="Giá bán")
    expiry_date = models.DateField(
        null=True, blank=True, verbose_name="Ngày hết hạn")
    supplier = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Nhà cung cấp")

    class Meta:
        verbose_name_plural = 'Product'

    def __str__(self):
        return f'{self.name} ({self.code})'


# =======================================================
#               MODEL GIAO DỊCH: PRESCRIPTION
#   Đại diện cho một toa thuốc tổng thể do bác sĩ kê cho bệnh nhân.
#   Phụ thuộc vào: Patient, User.
# =======================================================
class Prescription(models.Model):
    patient = models.ForeignKey(
        Patient, on_delete=models.SET_NULL, null=True, verbose_name="Full Name ")
    doctor = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, verbose_name="Bác sĩ")
    
    status = models.CharField(
        max_length=20, choices=PRESCRIPTION_STATUS_CHOICES, default='Pending', verbose_name="Trạng thái")
    
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Thời gian tạo")
    completed_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Thời gian hoàn tất")

    class Meta:
        verbose_name_plural = 'Prescription'

    def __str__(self):
        patient_name = self.patient.full_name if self.patient else "Không rõ"
        return f'Toa thuốc ID: {self.id} - Bệnh nhân: {patient_name}'



# =======================================================
#               MODEL GIAO DỊCH: ORDER
#   Ghi lại một giao dịch xuất kho (bán hàng).
#   Phụ thuộc vào: Prescription, Product, User.
# =======================================================
class Order(models.Model):
    prescription = models.ForeignKey(
        Prescription, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Từ toa thuốc")
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, null=True)
    staff = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True)
    order_quantity = models.PositiveIntegerField(null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Order'

    def __str__(self):
        staff_name = self.staff.username if self.staff else "N/A"
        product_name = self.product.name if self.product else "Sản phẩm đã xóa"
        return f'{product_name} - SL: {self.order_quantity or "N/A"} bởi {staff_name}'



# =======================================================
#               MODEL CHI TIẾT: PRESCRIPTIONDETAIL
#   Lưu trữ chi tiết từng loại thuốc trong một toa thuốc.
#   Phụ thuộc vào: Prescription, Product.
# =======================================================
class PrescriptionDetail(models.Model):
    prescription = models.ForeignKey(
        Prescription, on_delete=models.CASCADE, related_name='details', verbose_name="Toa thuốc")
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, null=True, verbose_name="Name")
    quantity = models.PositiveIntegerField(null=True, verbose_name="Quantity")
    is_collected = models.BooleanField(
        default=False, verbose_name="Đã lấy thuốc")

    class Meta:
        verbose_name_plural = 'Prescription Details'

    def __str__(self):
        product_name = self.product.name if self.product else "Sản phẩm đã xóa"
        return f'{product_name} - {self.quantity} (Toa: {self.prescription.id})'