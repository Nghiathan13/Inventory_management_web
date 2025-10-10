from .models import User, Product, Order, Prescription

def global_context(request):
    """
    Cung cấp các biến context dùng chung cho tất cả các template.
    """
    # Chỉ tính toán nếu người dùng đã đăng nhập để tối ưu hiệu suất
    if request.user.is_authenticated:
        workers_count = User.objects.count()
        products_count = Product.objects.count()
        orders_count = Order.objects.count()
        # Đây là biến mới để đếm số lượng toa thuốc đang chờ
        pending_prescriptions_count = Prescription.objects.filter(status='Pending').count()

        return {
            'workers_count': workers_count,
            'products_count': products_count,
            'orders_count': orders_count,
            'pending_prescriptions_count': pending_prescriptions_count,
        }
    return {}