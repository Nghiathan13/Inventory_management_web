# user/signals.py

from django.db.models.signals import post_save
from django.contrib.auth.models import User, Group
from django.dispatch import receiver
from .models import Profile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal này tự động tạo một Profile mỗi khi một User mới được tạo.
    """
    if created:
        Profile.objects.create(staff=instance)

@receiver(post_save, sender=Profile)
def add_user_to_group(sender, instance, created, **kwargs):
    """
    Signal này tự động cập nhật Group cho User dựa trên trường 'role'
    trong Profile của họ mỗi khi Profile được lưu.
    """
    user = instance.staff
    role = instance.role

    # Xóa người dùng khỏi tất cả các nhóm vai trò hiện có để tránh trùng lặp
    doctor_group = Group.objects.get(name='Doctor')
    supplier_group = Group.objects.get(name='Supplier')
    user.groups.remove(doctor_group, supplier_group)

    # Thêm người dùng vào nhóm tương ứng với vai trò
    if role == 'doctor':
        user.groups.add(doctor_group)
    elif role == 'supplier':
        user.groups.add(supplier_group)
    elif role == 'admin':
        # Đối với admin, chúng ta thường dùng cờ is_superuser
        user.is_superuser = True
        user.is_staff = True
        user.save()