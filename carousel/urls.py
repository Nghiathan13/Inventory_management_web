from django.urls import path
from . import views

app_name = 'carousel'

urlpatterns = [
    # URL cho trang điều khiển chính
    path('', views.control_panel, name='control_panel'),
    
    # URL để xem trạng thái hiện tại của kệ xoay
    path('api/status/', views.api_get_status, name='api_get_status'),
    
    # URL để gửi lệnh về vị trí "home"
    path('api/homing/', views.api_homing, name='api_homing'),
    
    # URL để di chuyển kệ đến một kệ cụ thể
    path('api/move/', views.api_move_to_shelf, name='api_move_to_shelf'),

]