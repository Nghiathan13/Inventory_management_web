# supplier/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from user.views import CustomLogoutView 

app_name = 'supplier' 

urlpatterns = [
    # URL login
    path('login/', auth_views.LoginView.as_view(
        template_name='supplier/login.html',
        redirect_authenticated_user=True 
    ), name='login'),
    
    # URL dashboard
    path('', views.supplier_dashboard, name='dashboard'),
    
    # URL xử lý và xác nhận đơn hàng
    path('order/process/<int:pk>/', views.process_order, name='process_order'),
    path('order/confirm/<int:pk>/', views.confirm_order_api, name='confirm_order_api'),

    # URL download pdf phiếu giao hàng
    path('delivery-note/download/<int:pk>/', views.download_delivery_note_pdf, name='download_delivery_note'),
    
    # URL logout
    path('logout/', CustomLogoutView.as_view(next_page='supplier:login'), name='logout'),
]