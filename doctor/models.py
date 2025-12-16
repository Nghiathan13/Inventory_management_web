from django.db import models
from django.contrib.auth.models import User
import uuid

# =======================================================
#               CÁC HẰNG SỐ LỰA CHỌN (CHOICES)
# =======================================================
PRESCRIPTION_STATUS_CHOICES = (
    ('Pending', 'Pending'),
    ('Dispensed', 'Dispensed'),
    ('Cancelled', 'Cancelled'),
)

# =======================================================
#               MODEL GIAO DỊCH: PRESCRIPTION
# =======================================================
class Prescription(models.Model):
    patient = models.ForeignKey(
        'patients.Patient', 
        on_delete=models.SET_NULL, 
        null=True, 
        verbose_name="Patient"
    )
    doctor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        verbose_name="Doctor"
    )
    status = models.CharField(
        max_length=20, 
        choices=PRESCRIPTION_STATUS_CHOICES, 
        default='Pending', 
        verbose_name="Status"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Created At"
    )
    completed_at = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="Completed At"
    )
    unique_code = models.UUIDField(
        default=uuid.uuid4, 
        editable=False, 
        unique=True
    )

    class Meta:
        db_table = 'dashboard_prescription'
        verbose_name_plural = 'Prescriptions'
        ordering = ['-created_at']

    def __str__(self):
        patient_name = self.patient.full_name if self.patient else "Unknown"
        return f'Prescription ID: #{self.id} - Patient: {patient_name}'

# =======================================================
#               MODEL CHI TIẾT: PRESCRIPTIONDETAIL
# =======================================================
class PrescriptionDetail(models.Model):
    prescription = models.ForeignKey(
        Prescription, 
        on_delete=models.CASCADE, 
        related_name='details', 
        verbose_name="Prescription"
    )
    product = models.ForeignKey(
        'products.Product', 
        on_delete=models.CASCADE, 
        null=True, 
        verbose_name="Product"
    )
    quantity = models.PositiveIntegerField(
        null=True, 
        verbose_name="Quantity"
    )
    uom = models.ForeignKey(
        'products.UnitOfMeasure', 
        on_delete=models.SET_NULL, 
        null=True, 
        verbose_name="Unit"
    )
    is_collected = models.BooleanField(
        default=False, 
        verbose_name="Collected"
    )

    class Meta:
        db_table = 'dashboard_prescriptiondetail'
        verbose_name_plural = 'Prescription Details'

    def __str__(self):
        product_name = self.product.name if self.product else "Deleted Product"
        return f'{self.quantity} {self.uom.name if self.uom else ""} {product_name} (Toa: #{self.prescription.id})'