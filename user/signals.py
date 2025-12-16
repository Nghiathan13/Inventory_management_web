from django.db.models.signals import post_save
from django.contrib.auth.models import User, Group
from django.dispatch import receiver
from .models import Profile

# =======================================================
#        TẠO HỒ SƠ NGƯỜI DÙNG (PROFILE CREATION)
# =======================================================
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(staff=instance)

# =======================================================
#        CẬP NHẬT NHÓM QUYỀN (GROUP ASSIGNMENT)
# =======================================================
@receiver(post_save, sender=Profile)
def add_user_to_group(sender, instance, created, **kwargs):
    user = instance.staff
    role = instance.role

    doctor_group, _ = Group.objects.get_or_create(name='Doctor')
    supplier_group, _ = Group.objects.get_or_create(name='Supplier')

    user.groups.remove(doctor_group, supplier_group)

    # Gán nhóm mới
    if role == 'doctor':
        user.groups.add(doctor_group)
        user.is_staff = False
        user.is_superuser = False
        
    elif role == 'supplier':
        user.groups.add(supplier_group)
        user.is_staff = False
        user.is_superuser = False
        
    elif role == 'admin':
        user.is_staff = True
        user.is_superuser = True
    user.save()