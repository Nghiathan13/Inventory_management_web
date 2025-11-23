# patients/models.py

from django.db import models
from datetime import date

# =======================================================
#               CÁC HẰNG SỐ LỰA CHỌN (CHOICES)
# =======================================================
GENDER_CHOICES = (
    ('Nam', 'Nam'),
    ('Nữ', 'Nữ'),
    ('Khác', 'Khác'),
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
# =======================================================
class Patient(models.Model):
    full_name = models.CharField(
        max_length=255, 
        verbose_name="Full Name"
    )
    date_of_birth = models.DateField(
        null=True, 
        blank=True, 
        verbose_name="Date of Birth"
    )
    gender = models.CharField(
        max_length=10, 
        choices=GENDER_CHOICES, 
        verbose_name="Gender"
    )
    address = models.CharField(
        max_length=255, 
        null=True, 
        blank=True, 
        verbose_name="Address"
    )
    phone_number = models.CharField(
        max_length=15, 
        null=True, 
        blank=True, 
        verbose_name="Phone Number"
    )
    avatar = models.ImageField(
        upload_to='patient_avatars/', 
        null=True, 
        blank=True, 
        verbose_name="Avatar"
    )
    citizen_id = models.CharField(
        max_length=20, 
        null=True, 
        blank=True, 
        unique=True, 
        verbose_name="Citizen ID"
    )
    health_insurance_id = models.CharField(
        max_length=20, 
        null=True, 
        blank=True, 
        verbose_name="Health Insurance ID"
    )
    ethnicity = models.CharField(
        max_length=50, 
        null=True, 
        blank=True, 
        verbose_name="Ethnicity"
    )
    blood_type = models.CharField(
        max_length=10, 
        choices=BLOOD_TYPE_CHOICES, 
        default='Unknown', 
        verbose_name="Blood Type"
    )
    allergies = models.TextField(
        null=True, 
        blank=True, 
        verbose_name="Allergies"
    )
    medical_history = models.TextField(
        null=True, 
        blank=True, 
        verbose_name="Medical History"
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = 'dashboard_patient'
        verbose_name_plural = 'Patients'
        ordering = ['-created_at']

    def __str__(self):
        return self.full_name

    @property
    def age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None