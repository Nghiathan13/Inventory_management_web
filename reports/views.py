# =======================================================
#               KHAI BÁO THƯ VIỆN (IMPORTS)
# =======================================================
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models.functions import TruncDate
from django.db.models import Count, Sum, F
from django.utils import timezone
from datetime import timedelta

# --- Models ---
from products.models import Product, ProductCategory, ProductBatch
from inventory.models import Order

# --- Decorators ---
from main.decorators import admin_required

# =======================================================
#               CÁC VIEW BÁO CÁO (REPORTS)
# =======================================================

# -------------------------------------------------------
#   BÁO CÁO TỔNG QUAN TỒN KHO
# -------------------------------------------------------
@login_required
@admin_required
def report_overview(request):
    # Dữ liệu cho biểu đồ Bar: Top 15 sản phẩm tồn kho nhiều nhất
    products_data = list(
        Product.objects.order_by('-quantity')[:15].values('name', 'quantity')
    )
    
    # Dữ liệu cho biểu đồ Pie: Phân bổ sản phẩm theo nhóm
    category_data = list(
        ProductCategory.objects.annotate(count=Count('product'))
        .filter(count__gt=0).values('name', 'count').order_by('-count')
    )

    context = {
        'products_data': products_data,
        'category_data': category_data,
        'active_report': 'overview'
    }
    return render(request, 'reports/overview.html', context)

# -------------------------------------------------------
#  BÁO CÁO PHÂN TÍCH XUẤT KHO
# -------------------------------------------------------
@login_required
@admin_required
def report_dispense_analysis(request):
    # Dữ liệu cho biểu đồ Doughnut: 10 sản phẩm bán chạy nhất
    dispense_data = list(
        Order.objects.values('product__name')
        .annotate(total_sold=Sum('order_quantity'))
        .order_by('-total_sold')[:10]
    )

    # Dữ liệu cho biểu đồ Line: Xu hướng bán hàng 7 ngày qua
    seven_days_ago = timezone.now() - timedelta(days=7)
    sales_trend_query = (
        Order.objects.filter(date__gte=seven_days_ago)
        .annotate(date_sold=TruncDate('date'))
        .values('date_sold')
        .annotate(count=Count('id'))
        .order_by('date_sold')
    )
    
    # Chuyển đổi định dạng ngày cho biểu đồ Line để Chart.js hiểu
    sales_trend_data = []
    for item in sales_trend_query:
        # Chỉ xử lý nếu date_sold CÓ dữ liệu (không phải None)
        if item['date_sold']: 
            sales_trend_data.append({
                'x': item['date_sold'].strftime('%Y-%m-%d'), 
                'y': item['count']
            })

    context = {
        'dispense_data': dispense_data,
        'sales_trend_data': sales_trend_data,
        'active_report': 'dispense'
    }
    return render(request, 'reports/dispense_analysis.html', context)

# -------------------------------------------------------
#   BÁO CÁO TRẠNG THÁI (Hết hàng/Hết hạn)
# -------------------------------------------------------
@login_required
@admin_required
def report_inventory_status(request):    
    # 1. Sản phẩm sắp hết hàng (Dựa vào tổng quantity trong Product)
    out_of_stock = Product.objects.filter(quantity__lte=F('reorder_point')).order_by('quantity')
    
    # 2. Lô hàng sắp hết hạn (Dựa vào ProductBatch)
    thirty_days_later = timezone.now().date() + timedelta(days=30)
    today = timezone.now().date()
    
    # Lấy các lô hàng còn số lượng > 0 và sắp hết hạn
    expiring_batches = ProductBatch.objects.filter(
        quantity__gt=0, # Chỉ quan tâm lô còn hàng
        expiry_date__lte=thirty_days_later,
        expiry_date__gte=today
    ).select_related('product').order_by('expiry_date')

    context = {
        'out_of_stock': out_of_stock,
        'expiring_batches': expiring_batches, # Đổi tên biến cho rõ nghĩa
        'active_report': 'status'
    }
    return render(request, 'reports/inventory_status.html', context)
