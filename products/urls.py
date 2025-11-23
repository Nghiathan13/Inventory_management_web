from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # --- URLs cho Product ---
    path('', views.product_list, name='list'),
    path('new/', views.product_add, name='add'),
    path('delete/<int:pk>/', views.product_delete, name='delete'),
    path('update/<int:pk>/', views.product_update, name='update'),
    path('detail/<int:pk>/', views.product_detail, name='detail'),
    path('locations/', views.manage_locations, name='manage_locations'),

    # --- URLs cho ProductCategory ---
    path('category/', views.category_list, name='category_list'),
    path('category/new/', views.category_form, name='category_add'),
    path('category/edit/<int:pk>/', views.category_form, name='category_edit'),
    path('category/detail/<int:pk>/', views.category_detail, name='category_detail'),
    path('category/delete/<int:pk>/', views.category_delete, name='category_delete'),

    # --- URLs cho UomCategory ---
    path('uom-category/', views.uom_category_list, name='uom_category_list'),
    path('uom-category/new/', views.uom_category_form, name='uom_category_add'),
    path('uom-category/edit/<int:pk>/', views.uom_category_form, name='uom_category_edit'),
    path('uom-category/detail/<int:pk>/', views.uom_category_detail, name='uom_category_detail'),
    path('uom-category/delete/<int:pk>/', views.uom_category_delete, name='uom_category_delete'),

    # --- URLs cho UnitOfMeasure (UoM) ---
    path('uom/', views.uom_list, name='uom_list'),
    path('uom/new/', views.uom_form, name='uom_add'),
    path('uom/edit/<int:pk>/', views.uom_form, name='uom_edit'),
    path('uom/detail/<int:pk>/', views.uom_detail, name='uom_detail'),
    path('uom/delete/<int:pk>/', views.uom_delete, name='uom_delete'),

    # --- URLs cho BillOfMaterials (BOM) ---
    path('bom/', views.bom_list, name='bom_list'),
    path('bom/new/', views.bom_form, name='bom_add'),
    path('bom/edit/<int:pk>/', views.bom_form, name='bom_edit'),
    path('bom/detail/<int:pk>/', views.bom_detail, name='bom_detail'),
    path('bom/delete/<int:pk>/', views.bom_delete, name='bom_delete'),
    
    # --- URL cho API ---
    path('api/search/', views.product_search_api, name='api_search'),
    path('api/location/batches-details/', views.api_get_product_batches_details, name='api_get_product_batches_details'),
    path('api/location/save/', views.api_save_location, name='api_save_location'),
]