from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # --- URLs cho Báo cáo ---
    path('', views.report_overview, name='overview'),
    path('dispense-analysis/', views.report_dispense_analysis, name='dispense_analysis'),
    path('inventory-status/', views.report_inventory_status, name='inventory_status'),
]