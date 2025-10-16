# =======================================================
#               KHAI BÁO THƯ VIỆN (IMPORTS)
# =======================================================
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views import View
from django import forms

# Decorators & Authentication
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.auth.views import PasswordResetView as BasePasswordResetView

# Models & Forms
from .models import Product, Order, Prescription, PrescriptionDetail, Patient, ProductCategory
from .forms import (
    ProductForm, OrderForm, PrescriptionForm,
    PrescriptionDetailForm, PatientForm, ProductCategoryForm
)

# Utilities
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist


# Import json
import json
from django.core.serializers.json import DjangoJSONEncoder

from django.db.models import Count, Sum
from datetime import datetime, timedelta

#Import BOM
from .models import BillOfMaterials, UnitOfMeasure
from .forms import BillOfMaterialsForm, UnitOfMeasureForm


# =======================================================
#               CÁC VIEW CHÍNH & DASHBOARD
# =======================================================

# -------------------------------------------------------
#   VIEW: TRANG CHỦ (DASHBOARD)
#   - View này vẫn cần giữ lại context vì nó truyền dữ liệu
#     cho biểu đồ (orders, products).
# -------------------------------------------------------
@login_required
def index(request):
    if request.user.is_staff or request.user.is_superuser:
        orders = Order.objects.all()
        products = Product.objects.all()
        context = {
            'orders': orders,
            'products': products,
        }
        return render(request, 'dashboard/index.html', context)
    else:
        return redirect('dashboard-prescription')


# -------------------------------------------------------
#   VIEW: TRANG LỊCH SỬ ĐƠN HÀNG (DÀNH CHO ADMIN)
# -------------------------------------------------------
@login_required
def order(request):
    orders = Order.objects.all().order_by('-date')
    context = {
        'orders': orders,
    }
    return render(request, 'dashboard/order/order.html', context)


# =======================================================
#               QUẢN LÝ ĐƠN VỊ TÍNH (UoM CRUD)
# =======================================================
@login_required
def uom_list(request):
    uoms = UnitOfMeasure.objects.all()
    return render(request, 'dashboard/uom/uom_list.html', {'uoms': uoms})

@login_required
def uom_form(request, pk=None):
    instance = get_object_or_404(UnitOfMeasure, pk=pk) if pk else None
    form = UnitOfMeasureForm(request.POST or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Unit of Measure saved successfully.')
        return redirect('dashboard-uom-list')
    title = 'Edit Unit of Measure' if instance else 'Create New Unit of Measure'
    context = {
        'form': form,
        'title': title,
    }
    return render(request, 'dashboard/uom/uom_form.html', context)

@login_required
def uom_delete(request, pk):
    uom = get_object_or_404(UnitOfMeasure, pk=pk)
    if request.method == 'POST':
        uom.delete()
        messages.success(request, f'Unit "{uom.name}" has been deleted.')
        return redirect('dashboard-uom-list')
    context = {
        'item': uom
    }
    return render(request, 'dashboard/uom/uom_confirm_delete.html', context)

# =======================================================
#               QUẢN LÝ BOM (BOM CRUD)
# =======================================================
@login_required
def bom_list(request):
    boms = BillOfMaterials.objects.select_related('product', 'uom_from', 'uom_to').all()
    context = {
        'boms': boms
    }
    return render(request, 'dashboard/bom/bom_list.html', context)

@login_required
def bom_form(request, pk=None):
    instance = get_object_or_404(BillOfMaterials, pk=pk) if pk else None
    form = BillOfMaterialsForm(request.POST or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Bill of Materials rule saved successfully.')
        return redirect('dashboard-bom-list')
    title = 'Edit BOM Rule' if instance else 'Create New BOM Rule'
    context = {
        'form': form,
        'title': title,
    }
    return render(request, 'dashboard/bom/bom_form.html', context)

@login_required
def bom_delete(request, pk):
    bom = get_object_or_404(BillOfMaterials, pk=pk)
    if request.method == 'POST':
        bom.delete()
        messages.success(request, 'BOM rule has been deleted.')
        return redirect('dashboard-bom-list')
    context =  {
        'item': bom
    }
    return render(request, 'dashboard/bom/bom_confirm_delete.html', context)

# =======================================================
#           QUẢN LÝ NHÓM SẢN PHẨM (CATEGORY CRUD)
# =======================================================
@login_required
def category_list(request):
    categories = ProductCategory.objects.all()
    context = {'categories': categories}
    return render(request, 'dashboard/product_category/category_list.html', context)

@login_required
def category_form(request, pk=None):
    if pk:
        instance = ProductCategory.objects.get(id=pk)
        title = "Sửa Nhóm Sản Phẩm"
    else:
        instance = None
        title = "Tạo Nhóm Sản Phẩm Mới"

    if request.method == 'POST':
        form = ProductCategoryForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, f'Đã lưu nhóm sản phẩm "{form.cleaned_data.get("name")}" thành công.')
            return redirect('dashboard-category-list')
    else:
        form = ProductCategoryForm(instance=instance)

    context = {'form': form, 'title': title, 'instance': instance}
    return render(request, 'dashboard/product_category/category_form.html', context)



# =======================================================
#               QUẢN LÝ KÊ ĐƠN (PRESCRIPTION)
# =======================================================

# -------------------------------------------------------
#   VIEW: TRANG KÊ ĐƠN THUỐC
# -------------------------------------------------------
@login_required
def prescription(request):
    if request.method == 'POST':
        prescription_form = PrescriptionForm(request.POST)
        if prescription_form.is_valid():
            try:
                with transaction.atomic():
                    new_prescription = prescription_form.save(commit=False)
                    new_prescription.doctor = request.user
                    new_prescription.status = 'Pending'
                    
                    form_count = int(request.POST.get('form_count', 0))
                    if form_count == 0 or not any(request.POST.get(f'details-{i}-product') for i in range(form_count)):
                        messages.error(request, 'Toa thuốc phải có ít nhất một loại thuốc.')
                        return redirect('dashboard-prescription')

                    details_to_process = []
                    processed_products = set()
                    for i in range(form_count):
                        product_id = request.POST.get(f'details-{i}-product')
                        quantity_str = request.POST.get(f'details-{i}-quantity')
                        uom_id = request.POST.get(f'details-{i}-uom')

                        if product_id and quantity_str and int(quantity_str) > 0:
                            if product_id in processed_products:
                                messages.error(request, f"Thuốc '{Product.objects.get(id=product_id).name}' đã được thêm. Vui lòng chỉnh sửa số lượng thay vì thêm dòng mới.")
                                return redirect('dashboard-prescription')
                            processed_products.add(product_id)
                            
                            product = Product.objects.get(id=int(product_id))
                            quantity = int(quantity_str)
                            uom_selected = UnitOfMeasure.objects.get(id=uom_id)

                            # =======================================================
                            #               LOGIC XỬ LÝ BOM
                            # =======================================================
                            quantity_to_deduct = quantity # Mặc định số lượng cần trừ

                            # Nếu đơn vị được chọn khác với đơn vị cơ bản của sản phẩm
                            if uom_selected != product.uom:
                                try:
                                    # Tìm quy tắc quy đổi trong BOM
                                    bom = BillOfMaterials.objects.get(
                                        product=product,
                                        uom_from=uom_selected,
                                        uom_to=product.uom # Đảm bảo quy đổi về đơn vị cơ bản
                                    )
                                    quantity_to_deduct = quantity * bom.conversion_factor
                                except BillOfMaterials.DoesNotExist:
                                    # Nếu không có quy tắc, báo lỗi
                                    messages.error(request, f"Không tìm thấy quy tắc quy đổi từ '{uom_selected.name}' sang '{product.uom.name}' cho sản phẩm '{product.name}'.")
                                    return redirect('dashboard-prescription')
                                
                            
                            # KIỂM TRA TỒN KHO VỚI SỐ LƯỢNG ĐÃ QUY ĐỔI
                            if product.quantity < quantity_to_deduct:
                                messages.error(request, f"Không đủ thuốc '{product.name}'. Cần {quantity_to_deduct} {product.uom.name} nhưng chỉ còn {product.quantity}.")
                                return redirect('dashboard-prescription')
                            

                            details_to_process.append({
                                'product': product,
                                'quantity': quantity,
                                'uom': uom_selected 
                            })
                    
                    # Logic lưu đã được sửa lại cho đúng quy trình mới
                    new_prescription.save()
                    for item in details_to_process:
                        PrescriptionDetail.objects.create(
                            prescription=new_prescription,
                            product=item['product'],
                            quantity=item['quantity'],
                            uom=item['uom']
                        )
                    
                    messages.success(request, f'Đã gửi toa thuốc cho bệnh nhân {new_prescription.patient.full_name} thành công.')
                    return redirect('dashboard-prescription')
            except Exception as e:
                messages.error(request, f'Đã có lỗi xảy ra: {e}')
        else:
            messages.error(request, 'Vui lòng kiểm tra lại thông tin, bạn có thể đã chưa chọn bệnh nhân.')
    
    # Logic cho phương thức GET
    prescription_form = PrescriptionForm()
    if request.user.is_staff or request.user.is_superuser:
        prescriptions = Prescription.objects.all().order_by('-created_at')
    else:
        prescriptions = Prescription.objects.filter(doctor=request.user).order_by('-created_at')
    context = {
        'prescription_form': prescription_form,
        'prescriptions': prescriptions,
        'products': Product.objects.all(),
        'uoms': UnitOfMeasure.objects.all(),
    }
    return render(request, 'dashboard/prescription/prescription.html', context)



# =======================================================
#               TRANG BÁO CÁO (REPORTS)
# =======================================================

# -------------------------------------------------------
#   VIEW 1: BÁO CÁO TỔNG QUAN TỒN KHO
# -------------------------------------------------------
@login_required
def report_overview(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard-index')

    # Dữ liệu cho biểu đồ Bar: Tồn kho
    products = Product.objects.order_by('-quantity')[:15]
    category_data = list(Product.objects.values('category').annotate(count=Count('id')).order_by('-count'))

    context = {
        'products': products, # Truyền trực tiếp QuerySet, xử lý trong template
        'category_json': json.dumps(category_data),
        'active_report': 'overview'
    }
    return render(request, 'dashboard/report/report_overview.html', context)

# -------------------------------------------------------
#   VIEW 2: BÁO CÁO PHÂN TÍCH XUẤT KHO
# -------------------------------------------------------
@login_required
def report_dispense_analysis(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard-index')

    # Dữ liệu cho biểu đồ Pie: Tỉ lệ sản phẩm đã bán
    dispense_data = list(
        Order.objects.values('product__name')
        .annotate(total_sold=Sum('order_quantity'))
        .order_by('-total_sold')[:10] # 10 sản phẩm bán chạy nhất
    )

    # Dữ liệu cho biểu đồ Line: Xu hướng bán hàng 7 ngày qua
    seven_days_ago = timezone.now() - timedelta(days=7)
    sales_trend = (
        Order.objects.filter(date__gte=seven_days_ago)
        .extra({'date_sold': "date(date)"})
        .values('date_sold')
        .annotate(count=Count('id'))
        .order_by('date_sold')
    )
    
    context = {
        'dispense_json': json.dumps(dispense_data),
        'trend_json': json.dumps(list(sales_trend), cls=DjangoJSONEncoder),
        'active_report': 'dispense'
    }
    return render(request, 'dashboard/report/report_dispense_analysis.html', context)

# -------------------------------------------------------
#   VIEW 3: BÁO CÁO TRẠNG THÁI (Hết hàng/Hết hạn)
# -------------------------------------------------------
@login_required
def report_inventory_status(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard-index')

    out_of_stock = Product.objects.filter(quantity__lte=10).order_by('quantity')
    expiring_soon = Product.objects.filter(
        expiry_date__lte=datetime.now() + timedelta(days=30),
        expiry_date__gte=datetime.now()
    ).order_by('expiry_date')

    context = {
        'out_of_stock': out_of_stock,
        'expiring_soon': expiring_soon,
        'active_report': 'status'
    }
    return render(request, 'dashboard/report/report_inventory_status.html', context)





# =======================================================
#               MODULE LẤY THUỐC (DISPENSE)
# =======================================================

# -------------------------------------------------------
#   VIEW: DANH SÁCH TOA THUỐC CHỜ LẤY
#   - Đã xóa bỏ các biến *_count không cần thiết.
# -------------------------------------------------------
@login_required
def dispense_list(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard-index')
        
    pending_prescriptions = Prescription.objects.filter(status='Pending').order_by('created_at')
    context = {
        'prescriptions': pending_prescriptions,
    }
    return render(request, 'dashboard/dispense/dispense_list.html', context)

# -------------------------------------------------------
#   VIEW: CHI TIẾT VÀ XỬ LÝ CẤP PHÁT THUỐC
#   - Logic chính giữ nguyên.
# -------------------------------------------------------
@login_required
def dispense_process(request, pk):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard-index')

    try:
        prescription = Prescription.objects.get(id=pk, status='Pending')
    except Prescription.DoesNotExist:
        messages.error(request, 'Toa thuốc này không tồn tại hoặc đã được xử lý.')
        return redirect('dispense-list')

    if request.method == 'POST':
        try:
            with transaction.atomic():
                details_to_dispense = request.POST.getlist('details')
                if not details_to_dispense:
                    messages.error(request, 'Bạn phải chọn ít nhất một loại thuốc để cấp phát.')
                    return redirect('dispense-process', pk=pk)
                
                for detail_id in details_to_dispense:
                    detail = PrescriptionDetail.objects.get(id=detail_id, prescription=prescription)
                    product = detail.product
                    prescribed_uom = detail.uom
                    prescribed_quantity = detail.quantity

                    quantity_to_deduct = prescribed_quantity # Mặc định
                    
                    # Nếu đơn vị kê đơn khác đơn vị cơ bản trong kho
                    if prescribed_uom and prescribed_uom != product.uom:
                        try:
                            bom_rule = BillOfMaterials.objects.get(
                                product=product,
                                uom_from=prescribed_uom,
                                uom_to=product.uom
                            )
                            quantity_to_deduct = prescribed_quantity * bom_rule.conversion_factor
                        except BillOfMaterials.DoesNotExist:
                            raise Exception(f"Không tìm thấy quy tắc quy đổi từ '{prescribed_uom.name}' sang '{product.uom.name}' cho '{product.name}'.")

                     # Kiểm tra tồn kho với số lượng ĐÃ QUY ĐỔI
                    if product.quantity < quantity_to_deduct:
                        raise Exception(f"Không đủ '{product.name}'. Cần {quantity_to_deduct} {product.uom.name} nhưng chỉ còn {product.quantity}.")
                    
                    #Trừ kho
                    product.quantity -= detail.quantity
                    product.save()

                    #Cập nhật trạng thái
                    detail.is_collected = True
                    detail.save()

                    #Tạo Order (lịch sử)
                    Order.objects.create(
                        product=product,
                        order_quantity=quantity_to_deduct,
                        staff=request.user,
                        prescription=prescription
                    )
                
                # Cập nhật trạng thái toa thuốc chính
                prescription.status = 'Dispensed'
                prescription.completed_at = timezone.now()
                prescription.save()
                
                messages.success(request, f'Đã cấp phát thuốc thành công cho toa #{prescription.id}.')
                return redirect('dispense-list')

        except Exception as e:
            messages.error(request, f'Lỗi: {e}')
            return redirect('dispense-process', pk=pk)

    context = {'prescription': prescription}
    return render(request, 'dashboard/dispense/dispense_process.html', context)


# =======================================================
#               QUẢN LÝ SẢN PHẨM (PRODUCT CRUD)
# =======================================================

# -------------------------------------------------------
#   VIEW: DANH SÁCH SẢN PHẨM (READ)
#   - Đã xóa bỏ các biến *_count không cần thiết.
# -------------------------------------------------------
@login_required
def product(request):
    search_query = request.GET.get('search', '')
    items = Product.objects.select_related('category').all()
    if search_query:
        items = items.filter(
            Q(name__icontains=search_query) | 
            Q(category__name__icontains=search_query) | 
            Q(code__icontains=search_query)
        )
    context = {
        'items': items,
        'search_query': search_query,
    }
    return render(request, 'dashboard/product/product.html', context)


# -------------------------------------------------------
#   VIEW: THÊM SẢN PHẨM (CREATE)
# -------------------------------------------------------
@login_required
def product_add(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            product_name = form.cleaned_data.get('name')
            messages.success(request, f'Thêm thuốc "{product_name}" thành công!')
            return redirect('dashboard-product')
    else:
        form = ProductForm()
    context = {
        'form': form,
        'title': 'New Medication'
    }
    return render(request, 'dashboard/product/product_form.html', context)


# -------------------------------------------------------
#   VIEW: CẬP NHẬT SẢN PHẨM (UPDATE)
# -------------------------------------------------------
@login_required
def product_update(request, pk):
    item = get_object_or_404(Product, id=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f'Cập nhật thuốc "{item.name}" thành công!')
            return redirect('dashboard-product')
    else:
        form = ProductForm(instance=item)
        context = {
            'form': form,
            'title': f'Chỉnh Sửa: {item.name}'
        }
    return render(request, 'dashboard/product/product_form.html', context)


# -------------------------------------------------------
#   VIEW: XÓA SẢN PHẨM (DELETE)
# -------------------------------------------------------
@login_required
def product_delete(request, pk):
    item = Product.objects.get(id=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, f'Đã xóa thuốc "{item.name}".')
        return redirect('dashboard-product')
    context = {'item': item}
    return render(request, 'dashboard/product/product_delete.html', context)


# -------------------------------------------------------
#   VIEW: CHI TIẾT SẢN PHẨM (READ DETAIL)
# -------------------------------------------------------
@login_required
def product_detail(request, pk):
    # Sử dụng get_object_or_404 để xử lý trường hợp không tìm thấy sản phẩm
    product = get_object_or_404(Product.objects.select_related('category'), pk=pk)
    
    # (Tùy chọn) Lấy lịch sử xuất kho của riêng sản phẩm này
    order_history = Order.objects.filter(product=product).select_related('staff', 'prescription__patient').order_by('-date')[:10]
    
    context = {
        'product': product,
        'order_history': order_history,
    }
    return render(request, 'dashboard/product/product_detail.html', context)

# =======================================================
#               QUẢN LÝ BỆNH NHÂN (PATIENT CRUD)
# =======================================================

# -------------------------------------------------------
#   VIEW: DANH SÁCH BỆNH NHÂN (READ)
# -------------------------------------------------------
@login_required
def patient_list(request):
    search_query = request.GET.get('search', '')
    if search_query:
        patients = Patient.objects.filter(full_name__icontains=search_query)
    else:
        patients = Patient.objects.all()
    context = {
        'patients': patients,
        'search_query': search_query,
    }
    return render(request, 'dashboard/patient/patient_list.html', context)


# -------------------------------------------------------
#   VIEW: THÊM BỆNH NHÂN (CREATE)
# -------------------------------------------------------
@login_required
def patient_add(request):
    if request.method == 'POST':
        form = PatientForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã thêm hồ sơ bệnh nhân mới thành công.')
            return redirect('dashboard-patient-list')
    else:
        form = PatientForm()
    context = {'form': form, 'title': 'Thêm Hồ Sơ Bệnh Nhân'}
    return render(request, 'dashboard/patient/patient_form.html', context)


# -------------------------------------------------------
#   VIEW: CẬP NHẬT BỆNH NHÂN (UPDATE)
# -------------------------------------------------------
@login_required
def patient_update(request, pk):
    patient = Patient.objects.get(id=pk)
    if request.method == 'POST':
        form = PatientForm(request.POST, request.FILES, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, f'Đã cập nhật hồ sơ cho bệnh nhân {patient.full_name}.')
            return redirect('dashboard-patient-list')
    else:
        form = PatientForm(instance=patient)
    context = {'form': form, 'title': 'Cập Nhật Hồ Sơ Bệnh Nhân'}
    return render(request, 'dashboard/patient/patient_form.html', context)


# -------------------------------------------------------
#   VIEW: XÓA BỆNH NHÂN (DELETE)
# -------------------------------------------------------
@login_required
def patient_delete(request, pk):
    patient = Patient.objects.get(id=pk)
    if request.method == 'POST':
        patient.delete()
        messages.success(request, f'Đã xóa hồ sơ của bệnh nhân {patient.full_name}.')
        return redirect('dashboard-patient-list')
    context = {'item': patient}
    return render(request, 'dashboard/patient/patient_confirm_delete.html', context)



# -------------------------------------------------------
#   VIEW: CHI TIẾT HỒ SƠ BỆNH NHÂN (READ DETAIL)
# -------------------------------------------------------
@login_required
def patient_detail(request, pk):
    try:
        patient = Patient.objects.get(id=pk)
        # Lấy lịch sử kê đơn của riêng bệnh nhân này
        prescriptions = Prescription.objects.filter(patient=patient).order_by('-created_at')
        context = {
            'patient': patient,
            'prescriptions': prescriptions,
        }
        return render(request, 'dashboard/patient/patient_detail.html', context)
    except Patient.DoesNotExist:
        messages.error(request, 'Hồ sơ bệnh nhân không tồn tại.')
        return redirect('dashboard-patient-list')
    

# =======================================================
#               QUẢN LÝ NHÂN VIÊN (STAFF)
# =======================================================

# -------------------------------------------------------
#   VIEW: DANH SÁCH NHÂN VIÊN
# -------------------------------------------------------
@login_required
def staff(request):
    workers = User.objects.all()
    context = {
        'workers': workers,
    }
    return render(request, 'dashboard/staff/staff.html', context)


# -------------------------------------------------------
#   VIEW: CHI TIẾT NHÂN VIÊN
# -------------------------------------------------------
@login_required
def staff_detail(request, pk):
    worker = User.objects.get(id=pk)
    context = {'worker': worker}
    return render(request, 'dashboard/staff/staff_detail.html', context)


# =======================================================
#           CÁC VIEW/CLASS XỬ LÝ MẬT KHẨU
# =======================================================
class UsernameResetForm(forms.Form):
    username = forms.CharField(max_length=150, label="Enter your username")

class UsernameResetView(View):
    template_name = 'user/username_reset.html'
    def get(self, request):
        return render(request, self.template_name, {'form': UsernameResetForm()})
    def post(self, request):
        form = UsernameResetForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            try:
                User.objects.get(username=username)
                request.session['reset_username'] = username
                return redirect('password_reset')
            except User.DoesNotExist:
                messages.error(request, "Username does not exist.")
        return render(request, self.template_name, {'form': form})

class CustomPasswordResetView(BasePasswordResetView):
    template_name = 'user/password_reset_form.html'
    def post(self, request, *args, **kwargs):
        username = request.session.get('reset_username')
        if not username:
            messages.error(request, "Please enter your username first.")
            return redirect('username-reset')
        try:
            user = User.objects.get(username=username)
            request.POST = request.POST.copy()
            request.POST['email'] = user.email
            return super().post(request, *args, **kwargs)
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('username-reset')