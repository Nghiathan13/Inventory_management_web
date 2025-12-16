from django.db import models
from django.contrib.auth.models import User

# =======================================================
#              SUPPLIERPROFILE
# =======================================================
class SupplierProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='supplier_profile')
    company_name = models.CharField(max_length=255, verbose_name="Company Name")
    contact_person = models.CharField(max_length=255, verbose_name="Contact Person")
    phone_number = models.CharField(max_length=20)
    address = models.TextField()

    def __str__(self):
        return self.company_name