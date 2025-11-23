from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages

# Models
from inventory.models import Order
from products.models import Product

# Decorators
from .decorators import admin_required, admin_or_doctor_required

# =======================================================
#               CÁC VIEW CHÍNH & ĐIỀU HƯỚNG
# =======================================================

# -------------------------------------------------------
#   VIEW: TRANG CHỦ (DASHBOARD)
# -------------------------------------------------------
@login_required
def index(request):
    if request.user.is_superuser:
        return redirect('main:admin_dashboard')
    elif request.user.groups.filter(name='Doctor').exists():
        return redirect('doctor:prescription')
    elif request.user.groups.filter(name='Supplier').exists():
        return redirect('supplier:dashboard')
    else:
        messages.error(request, "Tài khoản của bạn không được cấp quyền.")
        return redirect('user:login')

# -------------------------------------------------------
#   VIEW: TRANG CHỦ của ADMIN (DASHBOARD)
# -------------------------------------------------------
@login_required
@admin_required
def admin_dashboard(request):
    orders = Order.objects.all()
    products = Product.objects.all()

    context = {
        'orders': orders,
        'products': products,
    }

    return render(request, 'main/admin_dashboard.html', context)

# =======================================================
#               QUẢN LÝ NHÂN VIÊN (STAFF)
# =======================================================

# -------------------------------------------------------
#   VIEW: DANH SÁCH NHÂN VIÊN
# -------------------------------------------------------
@login_required
@admin_required
def staff_list(request):
    workers = User.objects.all()

    context = {
        'workers': workers
    }

    return render(request, 'staff/list.html', context)

# -------------------------------------------------------
#   VIEW: CHI TIẾT NHÂN VIÊN
# -------------------------------------------------------
@login_required
@admin_required
def staff_detail(request, pk):
    worker = User.objects.get(id=pk)

    context = {
        'worker': worker
    }
    
    return render(request, 'staff/detail.html', context)