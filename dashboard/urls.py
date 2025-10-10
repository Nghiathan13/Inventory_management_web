from django.urls import path,reverse_lazy
from . import views

urlpatterns = [
    path('', views.index, name='dashboard-index'),

    # Staff URLs
    path('staff/', views.staff, name='dashboard-staff'),
    path('staff/detail/<int:pk>/', views.staff_detail, name='dashboard-staff-detail'),
    
    # Product URLs
    path('product/', views.product, name='dashboard-product'),
    path('product/add/', views.product_add, name='dashboard-product-add'),
    path('product/delete/<int:pk>/', views.product_delete, name='dashboard-product-delete'),
    path('product/update/<int:pk>/', views.product_update, name='dashboard-product-update'),
    
    # Order URL
    path('order/', views.order, name='dashboard-order'),
    
    # Prescription URL
    path('prescription/', views.prescription, name='dashboard-prescription'),
    
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
    path('report/', views.report, name='dashboard-report'),

    path('username-reset/', views.UsernameResetView.as_view(), name='username-reset'),
    path('password-reset/', views.CustomPasswordResetView.as_view(
            template_name='user/password_reset_form.html',
            email_template_name='user/password_reset_email.html',
            success_url=reverse_lazy('password_reset_done')
        ), name='password_reset'),
]