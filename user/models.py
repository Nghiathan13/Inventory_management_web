# user/models.py

from django.db import models
from django.contrib.auth.models import User

# =======================================================
#               CÁC HẰNG SỐ LỰA CHỌN (CHOICES)
# =======================================================
ROLE_CHOICES = (
    ('doctor', 'Doctor'),
    ('admin', 'Admin'),
    ('supplier', 'Supplier'),
)


# =======================================================
#               MODEL: PROFILE
# =======================================================
class Profile(models.Model):
    staff = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile', 
        null=True
    )
    address = models.CharField(
        max_length=100, 
        null=True
    )
    phone = models.CharField(
        max_length=20, 
        null=True
    )
    image = models.ImageField(
        default='avatar.jpg', 
        upload_to='Profile_Images'
    )
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='doctor'
    )
    
    def __str__(self):
        return f'{self.staff.username}-Profile'