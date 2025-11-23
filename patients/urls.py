from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    # --- URLs cho Patient ---
    path('', views.patient_list, name='list'),
    path('new/', views.patient_add, name='add'),
    path('update/<int:pk>/', views.patient_update, name='update'),
    path('delete/<int:pk>/', views.patient_delete, name='delete'),
    path('detail/<int:pk>/', views.patient_detail, name='detail'),
]