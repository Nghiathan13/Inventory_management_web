from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from django.db import transaction, models
import json
import logging

# Models
from .models import Product, ProductCategory, UnitOfMeasure, UomCategory, BillOfMaterials, ProductBatch
from inventory.models import Order
from carousel.models import StockLocation, Shelf

# Forms 
from .forms import ProductForm, ProductCategoryForm, UnitOfMeasureForm, UomCategoryForm, BillOfMaterialsForm

# Decorators
from main.decorators import admin_required


logger = logging.getLogger(__name__)




# =======================================================
#        HELPER: THUẬT TOÁN QUY ĐỔI THÔNG MINH (BFS)
# =======================================================
def get_smart_conversion_factor(product_id, from_uom_id, to_uom_id, all_boms_list):
    if not from_uom_id or not to_uom_id: return 1
    if from_uom_id == to_uom_id: return 1

    # 1. Xây dựng đồ thị quy đổi cho sản phẩm này từ danh sách BOM
    graph = {}
    
    # Lọc các BOM rule liên quan đến product_id này
    relevant_boms = [b for b in all_boms_list if b['product_id'] == product_id]

    for bom in relevant_boms:
        # Cạnh xuôi: From -> To (Factor)
        if bom['uom_from_id'] not in graph: graph[bom['uom_from_id']] = []
        graph[bom['uom_from_id']].append({'to': bom['uom_to_id'], 'factor': float(bom['conversion_factor'])})
        
        # Cạnh ngược: To -> From (1 / Factor)
        if bom['uom_to_id'] not in graph: graph[bom['uom_to_id']] = []
        graph[bom['uom_to_id']].append({'to': bom['uom_from_id'], 'factor': 1.0 / float(bom['conversion_factor'])})

    # 2. Tìm đường đi ngắn nhất (BFS)
    queue = [{'id': from_uom_id, 'factor': 1.0}]
    visited = set()

    while queue:
        curr = queue.pop(0)
        if curr['id'] == to_uom_id:
            return curr['factor']

        visited.add(curr['id'])

        if curr['id'] in graph:
            for neighbor in graph[curr['id']]:
                if neighbor['to'] not in visited:
                    queue.append({
                        'id': neighbor['to'],
                        'factor': curr['factor'] * neighbor['factor'] # Tích lũy hệ số
                    })
    
    return 1

# =======================================================
#               QUẢN LÝ SẢN PHẨM (PRODUCT CRUD)
# =======================================================

# -------------------------------------------------------
#   VIEW: DANH SÁCH SẢN PHẨM (READ)
# -------------------------------------------------------
@login_required
@admin_required
def product_list(request):
    search_query = request.GET.get('search', '')
    items = Product.objects.select_related(
        'category', 
        'base_uom'
    ).prefetch_related(
        'locations__tray__shelf',
        'locations__quantity_uom',
        'locations__capacity_uom',
    ).all()

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
    return render(request, 'products/list.html', context)

# -------------------------------------------------------
#   VIEW: THÊM SẢN PHẨM (ADD)
# -------------------------------------------------------
@login_required
@admin_required
def product_add(request):
    """Xử lý việc thêm một sản phẩm mới (chỉ thông tin cơ bản)."""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Đã tạo thành công sản phẩm "{product.name}".')
            return redirect('products:list', pk=product.pk)
    else:
        form = ProductForm()
    
    all_uoms = UnitOfMeasure.objects.values('id', 'name', 'category_id')
    uoms_by_category = {}
    for uom in all_uoms:
        cat_id = uom['category_id']
        if cat_id not in uoms_by_category: uoms_by_category[cat_id] = []
        uoms_by_category[cat_id].append({'id': uom['id'], 'name': uom['name']})

    context = {
        'form': form, 
        'title': 'Thêm Sản Phẩm Mới',
        'uoms_by_category': uoms_by_category,
    }
    return render(request, 'products/form.html', context)


# -------------------------------------------------------
#   VIEW: CẬP NHẬT SẢN PHẨM (UPDATE)
# -------------------------------------------------------
@login_required
@admin_required
def product_update(request, pk):
    """Xử lý việc cập nhật thông tin cơ bản của sản phẩm."""
    item = get_object_or_404(Product, id=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f'Cập nhật thông tin cho "{item.name}" thành công!')
            return redirect('products:list')
    else:
        form = ProductForm(instance=item)

    all_uoms = UnitOfMeasure.objects.values('id', 'name', 'category_id')
    uoms_by_category = {}
    for uom in all_uoms:
        cat_id = uom['category_id']
        if cat_id not in uoms_by_category: uoms_by_category[cat_id] = []
        uoms_by_category[cat_id].append({'id': uom['id'], 'name': uom['name']})

    context = {
        'form': form, 
        'title': f'Chỉnh Sửa: {item.name}',
        'uoms_by_category': uoms_by_category,
    }
    return render(request, 'products/form.html', context)

# -------------------------------------------------------
#   VIEW: XÓA SẢN PHẨM (DELETE)
# -------------------------------------------------------
@login_required
@admin_required
def product_delete(request, pk):
    item = get_object_or_404(Product, id=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, f'Đã xóa thuốc "{item.name}".')
        return redirect('products:list')
    context = {
        'item': item
    }
    return render(request, 'products/confirm_delete.html', context)

# -------------------------------------------------------
#   VIEW: CHI TIẾT SẢN PHẨM (DETAIL)
# -------------------------------------------------------
@login_required
@admin_required
def product_detail(request, pk):
    """Hiển thị thông tin chi tiết của một sản phẩm."""
    product = get_object_or_404(
        Product.objects.prefetch_related(
            'locations__tray__shelf',
            'locations__quantity_uom',
            'locations__capacity_uom'
        ), 
        pk=pk
    )
    order_history = Order.objects.filter(product=product).select_related(
        'staff', 
        'prescription__patient'
    ).order_by('-date')[:10]

    all_boms_list = list(BillOfMaterials.objects.filter(product=product).values(
        'product_id', 
        'uom_from_id', 
        'uom_to_id', 
        'conversion_factor'
    ))

    batches_data = []
    all_batches = product.batches.all().order_by('expiry_date')

    total_allocated_product = 0 

    for batch in all_batches:
        allocated_qty_batch = 0
        locations = batch.batch_locations.all().select_related(
            'quantity_uom', 
            'tray__shelf'
        ) 

        for loc in locations:
            factor = get_smart_conversion_factor(
                product.id, 
                loc.quantity_uom_id, 
                product.base_uom_id, 
                all_boms_list
            )
            allocated_qty_batch += loc.quantity * factor

        
        allocated_qty_batch = round(allocated_qty_batch, 2)
        if allocated_qty_batch.is_integer(): allocated_qty_batch = int(allocated_qty_batch)

        # Tính tồn kho chưa phân bổ của Lô
        unallocated_qty_batch = batch.quantity - allocated_qty_batch
        if unallocated_qty_batch < 0: unallocated_qty_batch = 0
        
        # Cộng dồn vào tổng sản phẩm
        total_allocated_product += allocated_qty_batch
        
        batches_data.append({
            'obj': batch,
            'allocated': allocated_qty_batch,
            'unallocated': unallocated_qty_batch,
            'locations': locations
        })

    total_unallocated_product = product.quantity - total_allocated_product
    if total_unallocated_product < 0: total_unallocated_product = 0

    context = {
        'product': product, 
        'order_history': order_history,
        'batches_data': batches_data,
        'calculated_allocated': total_allocated_product,
        'calculated_unallocated': total_unallocated_product,
    }
    return render(request, 'products/detail.html', context)

# =======================================================
#           QUẢN LÝ NHÓM SẢN PHẨM (PRODUCT CATEGORY)
# =======================================================

# -------------------------------------------------------
#   VIEW: DANH SÁCH NHÓM SẢN PHẨM (READ)
# -------------------------------------------------------
@login_required
@admin_required
def category_list(request):
    categories = ProductCategory.objects.all()
    context = {
        'categories': categories
    }
    return render(request, 'product_category/list.html', context)

# -------------------------------------------------------
#   VIEW: FORM THÊM/SỬA NHÓM SẢN PHẨM (CREATE/UPDATE)
# -------------------------------------------------------    
@login_required
@admin_required
def category_form(request, pk=None):
    if pk:
        instance = ProductCategory.objects.get(id=pk)
        title = "Edit Medication Category"
    else:
        instance = None
        title = "Create New Medication Category"

    if request.method == 'POST':
        form = ProductCategoryForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, f'Đã lưu nhóm sản phẩm "{form.cleaned_data.get("name")}" thành công.')
            return redirect('products:category_list')
    else:
        form = ProductCategoryForm(instance=instance)
    context = {
        'form': form, 
        'title': title, 
        'instance': instance
    }
    return render(request, 'product_category/form.html', context)

# -------------------------------------------------------
#   VIEW: XEM CHI TIẾT NHÓM SẢN PHẨM (READ DETAIL)
# -------------------------------------------------------
@login_required
@admin_required
def category_detail(request, pk):
    category = get_object_or_404(ProductCategory.objects.prefetch_related('children', 'product_set'), pk=pk)
    context = {
        'category': category
        }
    return render(request, 'product_category/detail.html', context)

# -------------------------------------------------------
#   VIEW: XÁC NHẬN XÓA NHÓM SẢN PHẨM (DELETE)
# -------------------------------------------------------
@login_required
@admin_required
def category_delete(request, pk):
    category = get_object_or_404(ProductCategory, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, f'Product Category "{category.name}" has been deleted.')
        return redirect('products:category_list')
    return render(request, 'product_category/confirm_delete.html', {'item': category})

# =======================================================
#           QUẢN LÝ NHÓM ĐƠN VỊ TÍNH (UoM CATEGORY)
# =======================================================

# -------------------------------------------------------
#   VIEW: DANH SÁCH NHÓM ĐƠN VỊ TÍNH (READ)
# -------------------------------------------------------
@login_required
@admin_required
def uom_category_list(request):
    categories = UomCategory.objects.all().order_by('name')
    context = {
        'categories': categories
    }
    return render(request, 'uom_category/list.html', context)

# -------------------------------------------------------
#   VIEW: FORM THÊM/SỬA NHÓM ĐƠN VỊ TÍNH (CREATE/UPDATE)
# -------------------------------------------------------
@login_required
@admin_required
def uom_category_form(request, pk=None):
    instance = get_object_or_404(UomCategory, pk=pk) if pk else None
    form = UomCategoryForm(request.POST or None, instance=instance)
    if form.is_valid():
        form.save()
        messages.success(request, 'Đã lưu nhóm đơn vị tính.')
        return redirect('products:uom_category_list')
        
    title = 'Sửa Nhóm Đơn Vị Tính' if instance else 'Tạo Nhóm Đơn Vị Tính Mới'
    context = {
        'form': form, 
        'title': title
    }
    return render(request, 'uom_category/form.html', context)

# -------------------------------------------------------
#   VIEW: XEM CHI TIẾT MỘT NHÓM ĐƠN VỊ TÍNH (READ DETAIL)
# -------------------------------------------------------
@login_required
@admin_required
def uom_category_detail(request, pk):
    category = get_object_or_404(UomCategory.objects.prefetch_related('uoms'), pk=pk)
    context = {
        'category': category
    }
    return render(request, 'uom_category/detail.html', context)

# -------------------------------------------------------
#   VIEW: XÁC NHẬN XÓA NHÓM ĐƠN VỊ TÍNH (DELETE)
# -------------------------------------------------------
@login_required
@admin_required
def uom_category_delete(request, pk):
    category = get_object_or_404(UomCategory, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, f'UoM Category "{category.name}" has been deleted.')
        return redirect('products:uom_category_list')
    return render(request, 'uom_category/confirm_delete.html', {'item': category})

# =======================================================
#               QUẢN LÝ ĐƠN VỊ TÍNH (UoM)
# =======================================================

# -------------------------------------------------------
#   VIEW: DANH SÁCh ĐƠN VỊ (READ)
# -------------------------------------------------------
@login_required
@admin_required
def uom_list(request):
    uoms = UnitOfMeasure.objects.all()
    context = {
        'uoms': uoms
    }
    return render(request, 'uom/list.html', context)

# -------------------------------------------------------
#   VIEW: FORM THÊM/SỬA ĐƠN VỊ (CREATE/UPDATE)
# -------------------------------------------------------
@login_required
@admin_required
def uom_form(request, pk=None):
    instance = get_object_or_404(UnitOfMeasure, pk=pk) if pk else None
    form = UnitOfMeasureForm(request.POST or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Unit of Measure saved successfully.')
        return redirect('products:uom_list')
    title = 'Edit Unit of Measure' if instance else 'Create New Unit of Measure'
    context = {
        'form': form,
        'title': title,
        'instance': instance,
    }
    return render(request, 'uom/form.html', context)

# -------------------------------------------------------
#   VIEW: XEM CHI TIẾT MỘT ĐƠN VỊ TÍNH (READ DETAIL)
# -------------------------------------------------------
@login_required
@admin_required
def uom_detail(request, pk):
    uom = get_object_or_404(UnitOfMeasure.objects.select_related('category'), pk=pk)
    context = {
        'uom': uom
    }
    return render(request, 'uom/detail.html', context)

# -------------------------------------------------------
#   VIEW: XÁC NHẬN XÓA ĐƠN VỊ (DELETE)
# -------------------------------------------------------
@login_required
@admin_required
def uom_delete(request, pk):
    uom = get_object_or_404(UnitOfMeasure, pk=pk)
    if request.method == 'POST':
        uom.delete()
        messages.success(request, f'Unit "{uom.name}" has been deleted.')
        return redirect('products:uom_list')
    context = {
        'item': uom
    }
    return render(request, 'uom/confirm_delete.html', context)

# =======================================================
#               QUẢN LÝ BẢNG QUY ĐỔI (BOM)
# =======================================================

# -------------------------------------------------------
#   VIEW: DANH SÁCH CÁC QUY TẮC BOM (READ)
# -------------------------------------------------------
@login_required
@admin_required
def bom_list(request):
    boms = BillOfMaterials.objects.select_related('product', 'uom_from', 'uom_to').all().order_by('product__name')
    context = {
        'boms': boms
    }
    return render(request, 'bom/list.html', context)

# -------------------------------------------------------
#   VIEW: FORM THÊM/SỬA MỘT QUY TẮC BOM (CREATE/UPDATE)
# -------------------------------------------------------
@login_required
@admin_required
def bom_form(request, pk=None):
    instance = get_object_or_404(BillOfMaterials, pk=pk) if pk else None
    form = BillOfMaterialsForm(request.POST or None, instance=instance)
    if form.is_valid():
        form.save()
        messages.success(request, 'Đã lưu quy tắc quy đổi.')
        return redirect('products:bom_list')
        
    title = 'Sửa Quy Tắc' if instance else 'Tạo Quy Tắc Mới'

    # 1. Lấy danh sách sản phẩm và ID nhóm UoM của chúng
    products_with_uom_cat = list(Product.objects.filter(
        uom_category__isnull=False
    ).values('id', 'uom_category_id'))

    # 2. Lấy tất cả UoM và nhóm chúng theo category_id
    all_uoms = UnitOfMeasure.objects.values('id', 'name', 'category_id')
    uoms_by_category = {}
    for uom in all_uoms:
        cat_id = uom['category_id']
        if cat_id not in uoms_by_category:
            uoms_by_category[cat_id] = []
        uoms_by_category[cat_id].append({'id': uom['id'], 'name': uom['name']})

    context = {
        'form': form, 
        'title': title,
        'products_with_uom_cat_json': json.dumps(products_with_uom_cat),
        'uoms_by_category_json': json.dumps(uoms_by_category),
    }
    return render(request, 'bom/form.html', context)

# -------------------------------------------------------
#   VIEW: XEM CHI TIẾT MỘT QUY TẮC BOM (READ DETAIL)
# -------------------------------------------------------
@login_required
@admin_required
def bom_detail(request, pk):
    bom = get_object_or_404(BillOfMaterials.objects.select_related('product', 'uom_from', 'uom_to'), pk=pk)
    context = {
        'bom': bom
    }
    return render(request, 'bom/detail.html', context)

# -------------------------------------------------------
#   VIEW: XÁC NHẬN XÓA MỘT QUY TẮC BOM (DELETE)
# -------------------------------------------------------
@login_required
@admin_required
def bom_delete(request, pk):
    bom = get_object_or_404(BillOfMaterials, pk=pk)
    if request.method == 'POST':
        bom.delete()
        messages.success(request, 'BOM rule has been deleted.')
        return redirect('products:bom_list')
    context = {
        'item': bom
    }
    return render(request, 'bom/confirm_delete.html', context)

# =======================================================
#               API ENDPOINTS (CHO JAVASCRIPT)
# =======================================================
@login_required
@admin_required
def product_search_api(request):
    query = request.GET.get('q', '')
    if len(query) >= 2:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(code__icontains=query) |
            Q(category__name__icontains=query)
        ).select_related('category', 'uom')[:10] 
        
        results = [
            {
                'id': p.id,
                'name': p.name,
                'code': p.code,
                'category': p.category.name if p.category else 'N/A',
                'quantity': p.quantity,
                'uom': p.uom.name if p.uom else 'N/A',
                'url': reverse('products:detail', args=[p.id])
            }
            for p in products
        ]
    else:
        results = []
    return JsonResponse(results, safe=False)


# =======================================================
#           QUẢN LÝ VỊ TRÍ TỔNG THỂ 
# =======================================================

@login_required
@admin_required
def manage_locations(request):
    """
    Hiển thị giao diện quản lý vị trí tổng thể cho tất cả các kệ.
    """
    all_shelves = Shelf.objects.prefetch_related(
        'trays',
        'trays__location__product', 
        'trays__location__batch', 
        'trays__location__quantity_uom',
        'trays__location__capacity_uom',
    ).all()
    
    # Lấy tất cả sản phẩm
    all_products_data = list(Product.objects.values(
        'id', 
        'name', 
        'quantity', 
        'uom_category_id', 
        'base_uom__name',
        'base_uom_id',
    ))
        
    # Lấy dữ liệu đơn vị tính đã phân loại theo category
    all_uoms = UnitOfMeasure.objects.values('id', 'name', 'category_id')
    uoms_by_category = {}
    for uom in all_uoms:
        cat_id = uom['category_id']
        if cat_id not in uoms_by_category: 
            uoms_by_category[cat_id] = []
        uoms_by_category[cat_id].append({'id': uom['id'], 'name': uom['name']})
    
    # Lấy thông tin tất cả các vị trí đã được gán để tính toán số lượng đã phân bổ
    all_locations_data = []
    locations = StockLocation.objects.select_related(
        'product', 
        'batch', 
        'quantity_uom', 
        'capacity_uom'
    ).all()

    all_boms_data = list(BillOfMaterials.objects.values(
        'product_id', 
        'uom_from_id', 
        'uom_to_id', 
        'conversion_factor'
    ))
    safe_boms_data = []
    for bom in all_boms_data:
        safe_boms_data.append({
            'product_id': bom['product_id'],
            'uom_from_id': bom['uom_from_id'],
            'uom_to_id': bom['uom_to_id'],
            'conversion_factor': float(bom['conversion_factor']) 
        })

    for loc in locations:
        all_locations_data.append({
            'tray_id': loc.tray_id,
            'product_id': loc.product_id,
            'batch_id': loc.batch_id,
            'batch_number': loc.batch.batch_number if loc.batch else '',
            'quantity': loc.quantity,
            'quantity_uom_id': loc.quantity_uom_id,    
            'quantity_uom_name': loc.quantity_uom.name if loc.quantity_uom else '',
            'capacity': loc.capacity,
            'capacity_uom_id': loc.capacity_uom_id,    
            'capacity_uom_name': loc.capacity_uom.name if loc.capacity_uom else '',
            'percent': 0
        })

    context = {
        'all_shelves': all_shelves,
        'all_products_data': all_products_data,
        'uoms_by_category': uoms_by_category,
        'all_locations_data': all_locations_data,
        'all_boms_data': all_boms_data,
    }
    return render(request, 'products/manage_locations.html', context)

# -------------------------------------------------------
#   API: LẤY CHI TIẾT LÔ VÀ TỒN KHO (Unallocated)
# -------------------------------------------------------
@login_required
@admin_required
def api_get_product_batches_details(request):
    """
    API trả về danh sách các Lô của một sản phẩm.
    """
    product_id = request.GET.get('product_id')
    if not product_id:
        return JsonResponse({'status': 'error', 'message': 'Missing product ID'})
    
    product = get_object_or_404(Product, pk=product_id)
    
    all_boms_list = list(BillOfMaterials.objects.filter(product=product).values(
        'product_id', 
        'uom_from_id', 
        'uom_to_id', 
        'conversion_factor'
    ))

    batches = product.batches.filter(quantity__gt=0).order_by('expiry_date')
    batches_data = []
    
    for batch in batches:
        total_batch_qty = batch.quantity
        locations = batch.batch_locations.select_related('quantity_uom')
        allocated_qty_base = 0
        
        for loc in locations:
            factor = get_smart_conversion_factor(product.id, loc.quantity_uom_id, product.base_uom_id, all_boms_list)
            allocated_qty_base += loc.quantity * factor
            

        allocated_qty_base = round(allocated_qty_base, 2)
        if allocated_qty_base.is_integer(): allocated_qty_base = int(allocated_qty_base)

        unallocated_qty = total_batch_qty - allocated_qty_base
        if unallocated_qty < 0: unallocated_qty = 0

        batches_data.append({
            'id': batch.id,
            'batch_number': batch.batch_number,
            'expiry': batch.expiry_date.strftime('%d/%m/%Y'),
            'total': total_batch_qty,
            'allocated': allocated_qty_base,
            'unallocated': unallocated_qty
        })

    return JsonResponse({
        'status': 'ok',
        'base_uom': product.base_uom.name if product.base_uom else '',
        'batches': batches_data
    })


# -------------------------------------------------------
#   API: LƯU VỊ TRÍ
# -------------------------------------------------------
@login_required
@admin_required
@require_POST
def api_save_location(request):
    try:
        data = json.loads(request.body)
        tray_id = data.get('tray_id')
        batch_id = data.get('batch_id')
        
        if not tray_id:
            return JsonResponse({'status': 'error', 'message': 'Thiếu Tray ID'}, status=400)

        with transaction.atomic():
            StockLocation.objects.filter(tray_id=tray_id).delete()
            
            if batch_id: # Nếu không phải lệnh xóa
                qty = int(data.get('quantity', 0))
                qty_uom_id = data.get('quantity_uom_id')
                cap = int(data.get('capacity', 50))
                cap_uom_id = data.get('capacity_uom_id')

                batch = get_object_or_404(ProductBatch, pk=batch_id)
                
                StockLocation.objects.create(
                    tray_id=tray_id,
                    product=batch.product,
                    batch=batch,
                    quantity=qty,
                    quantity_uom_id=qty_uom_id,
                    capacity=cap,
                    capacity_uom_id=cap_uom_id
                )
        
        return JsonResponse({'status': 'ok'})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)