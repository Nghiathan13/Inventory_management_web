from django.urls import path
from . import views

app_name = 'doctor'

urlpatterns = [
    # --- URLs cho Prescription ---
    path('prescription/', views.prescription, name='prescription'),
    path('prescription/download/<int:pk>/', views.download_prescription_pdf, name='download_prescription_pdf'),
]