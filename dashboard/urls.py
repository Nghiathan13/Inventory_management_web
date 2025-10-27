from django.urls import path, reverse_lazy , reverse
from . import views

urlpatterns = [
    path('', views.index, name='dashboard-index'),

    # Staff URLs
    path('staff/', views.staff, name='dashboard-staff'),
    path('staff/detail/<int:pk>/', views.staff_detail, name='dashboard-staff-detail'),
    
    # Product URLs
    path('product/', views.product, name='dashboard-product'),
    path('product/new/', views.product_add, name='dashboard-product-add'),
    path('product/delete/<int:pk>/', views.product_delete, name='dashboard-product-delete'),
    path('product/update/<int:pk>/', views.product_update, name='dashboard-product-update'),
    path('product/detail/<int:pk>/', views.product_detail, name='dashboard-product-detail'),

    # URLs cho Nhóm Sản phẩm
    path('product-category/', views.category_list, name='dashboard-category-list'),
    path('product-category/new/', views.category_form, name='dashboard-category-add'),
    path('product-category/edit/<int:pk>/', views.category_form, name='dashboard-category-edit'),
    path('product-category/detail/<int:pk>/', views.category_detail, name='dashboard-category-detail'),
    path('product-category/delete/<int:pk>/', views.category_delete, name='dashboard-category-delete'),

    # URLs cho UoM Category
    path('product/uom-category/', views.uom_category_list, name='dashboard-uom-category-list'),
    path('product/uom-category/new/', views.uom_category_form, name='dashboard-uom-category-add'),
    path('product/uom-category/edit/<int:pk>/', views.uom_category_form, name='dashboard-uom-category-edit'),
    path('product/uom-category/detail/<int:pk>/', views.uom_category_detail, name='dashboard-uom-category-detail'),
    path('product/uom-category/delete/<int:pk>/', views.uom_category_delete, name='dashboard-uom-category-delete'),

    # URLs cho UoM
    path('product/uom/new/', views.uom_form, name='dashboard-uom-add'),
    path('product/uom/edit/<int:pk>/', views.uom_form, name='dashboard-uom-edit'),
    path('product/uom/detail/<int:pk>/', views.uom_detail, name='dashboard-uom-detail'),
    path('product/uom/delete/<int:pk>/', views.uom_delete, name='dashboard-uom-delete'),
    path('product/uom/', views.uom_list, name='dashboard-uom-list'),

    # URLs cho BOM
    path('product/bom/', views.bom_list, name='dashboard-bom-list'),
    path('product/bom/new/', views.bom_form, name='dashboard-bom-add'),
    path('product/bom/detail/<int:pk>/', views.bom_detail, name='dashboard-bom-detail'),
    path('product/bom/edit/<int:pk>/', views.bom_form, name='dashboard-bom-edit'),
    path('product/bom/delete/<int:pk>/', views.bom_delete, name='dashboard-bom-delete'),

    # Order URL
    path('order/', views.order, name='dashboard-order'),
    
    # Prescription URL
    path('prescription/', views.prescription, name='dashboard-prescription'),
    path('prescription/download/<int:pk>/', views.download_prescription_pdf, name='download-prescription-pdf'),
    
    # Patient URLs
    path('patient/', views.patient_list, name='dashboard-patient-list'),
    path('patient/detail/<int:pk>/', views.patient_detail, name='dashboard-patient-detail'),
    path('patient/add/', views.patient_add, name='dashboard-patient-add'),
    path('patient/update/<int:pk>/', views.patient_update, name='dashboard-patient-update'),
    path('patient/delete/<int:pk>/', views.patient_delete, name='dashboard-patient-delete'),

    # Dispense URLs
    path('dispense/', views.dispense_list, name='dispense-list'),
    path('dispense/process/<int:pk>/', views.dispense_process, name='dispense-process'),
    
    # Report URL
    path('report/', views.report_overview, name='dashboard-report-overview'),
    path('report/dispense-analysis/', views.report_dispense_analysis, name='dashboard-report-dispense'),
    path('report/inventory-status/', views.report_inventory_status, name='dashboard-report-status'),

    path('username-reset/', views.UsernameResetView.as_view(), name='username-reset'),
    path('password-reset/', views.CustomPasswordResetView.as_view(
            template_name='user/password_reset_form.html',
            email_template_name='user/password_reset_email.html',
            success_url=reverse_lazy('password_reset_done')
        ), name='password_reset'),

    
    # URL cho API tìm kiếm gợi ý
    path('api/product-search/', views.product_search_api, name='api-product-search'),

]