from django.core.exceptions import PermissionDenied
from functools import wraps

# =======================================================
#               DECORATOR: ADMIN_REQUIRED
# =======================================================
def admin_required(function):
    """
    Decorator này đảm bảo chỉ có superuser (Admin/Dược sĩ) mới có thể truy cập view.
    """
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.is_superuser:
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrap

# =======================================================
#               DECORATOR: DOCTOR_REQUIRED
# =======================================================
def doctor_required(function):
    """
    Decorator này đảm bảo chỉ người dùng thuộc nhóm 'Doctor' mới có thể truy cập view.
    """
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.groups.filter(name='Doctor').exists():
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrap

# =======================================================
#               DECORATOR: ADMIN_OR_DOCTOR_REQUIRED
# =======================================================
def admin_or_doctor_required(function):
    """
    Decorator cho phép Admin (superuser) HOẶC Bác sĩ (nhóm 'Doctor') truy cập.
    """
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.is_superuser or request.user.groups.filter(name='Doctor').exists():
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrap

# =======================================================
#               DECORATOR: SUPPLIER_REQUIRED
# =======================================================
def supplier_required(function):
    """
    Decorator cho phép chỉ người dùng thuộc nhóm 'Supplier' truy cập view.
    """
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.groups.filter(name='Supplier').exists():
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrap
