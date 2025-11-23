from django.urls import path
from . import views

# app_name giúp tạo namespace cho các URL, ví dụ: {% url 'main:admin_dashboard' %}
app_name = 'main'

urlpatterns = [
    # URL Gốc: Trỏ đến view điều hướng
    path('', views.index, name='index'),
    
    # URL cho trang dashboard chính của Admin
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # --- URLs cho quản lý Staff ---
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/detail/<int:pk>/', views.staff_detail, name='staff_detail'),
]