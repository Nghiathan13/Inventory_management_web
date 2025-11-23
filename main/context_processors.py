from django.contrib.auth.models import User
from products.models import Product
from inventory.models import Order
from doctor.models import Prescription

def global_context(request):
    if request.user.is_authenticated and request.user.is_superuser:
        workers_count = User.objects.count()
        products_count = Product.objects.count()
        orders_count = Order.objects.count()
        pending_prescriptions_count = Prescription.objects.filter(status='Pending').count()

        return {
            'workers_count': workers_count,
            'products_count': products_count,
            'orders_count': orders_count,
            'pending_prescriptions_count': pending_prescriptions_count,
        }
    return {}