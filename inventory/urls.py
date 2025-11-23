from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # --- URL cho Lịch sử xuất kho ---
    path('history/', views.order_history, name='order_history'),
    
    # --- URLs cho Cấp phát thuốc (Dispense) ---
    path('dispense/', views.dispense_list, name='dispense_list'),
    path('dispense/process/<int:pk>/', views.dispense_process, name='dispense_process'),
    
    # --- URLs cho Đặt hàng (Purchasing) ---
    path('purchasing/', views.reorder_list, name='reorder_list'),
    path('purchasing/create/', views.create_purchase_order, name='create_po'),
    path('purchasing/detail/<int:pk>/', views.purchase_order_detail, name='po_detail'),
    
    # --- URLs cho Nhập kho (Stock-in) ---
    path('stock-in/scan/', views.stock_in_scan, name='stock_in_scan'),
    path('stock-in/receive/<uuid:po_code>/', views.receive_purchase_order, name='receive_po'),
    path('api/stock-in/process/<uuid:detail_code>/', views.stock_in_process_api, name='stock_in_process_api'),

    # --- URLs CHO NHẬP KHO THỦ CÔNG ---
    path('receive/manual/', views.manual_receive_list, name='manual_receive_list'),
    path('receive/manual/<int:po_pk>/', views.manual_receive_order, name='manual_receive_order'),
    path('receive/manual/update-item/<int:detail_pk>/', views.manual_update_item, name='manual_update_item'),

    # --- API CHO QUY TRÌNH PICKING ---
    path('api/picking/calculate/<int:prescription_id>/', views.api_calculate_picking_path, name='api_calculate_picking_path'),
    path('api/picking/confirm/', views.api_confirm_pick, name='api_confirm_pick'),
    path('api/picking/undo/', views.api_undo_pick, name='api_undo_pick'),
]