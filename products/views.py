from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from django.db import transaction
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
#               HELPER FUNCTIONS
# =======================================================

# -------------------------------------------------------
#   CALCULATE CONVERSION FACTOR (BFS)
# -------------------------------------------------------
def get_smart_conversion_factor(product_id, from_uom_id, to_uom_id, all_boms_list):
    if not from_uom_id or not to_uom_id: return 1
    if from_uom_id == to_uom_id: return 1

    graph = {}
    relevant_boms = [b for b in all_boms_list if b['product_id'] == product_id]

    for bom in relevant_boms:
        if bom['uom_from_id'] not in graph: graph[bom['uom_from_id']] = []
        graph[bom['uom_from_id']].append({'to': bom['uom_to_id'], 'factor': float(bom['conversion_factor'])})
        
        if bom['uom_to_id'] not in graph: graph[bom['uom_to_id']] = []
        graph[bom['uom_to_id']].append({'to': bom['uom_from_id'], 'factor': 1.0 / float(bom['conversion_factor'])})

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
                    queue.append({'id': neighbor['to'], 'factor': curr['factor'] * neighbor['factor']})
    
    return 1


# =======================================================
#               PRODUCT MANAGEMENT
# =======================================================

# -------------------------------------------------------
#   PRODUCT LIST
# -------------------------------------------------------
@login_required
@admin_required
def product_list(request):
    search_query = request.GET.get('search', '')
    items = Product.objects.select_related('category', 'base_uom').prefetch_related(
        'locations__tray__shelf', 'locations__quantity_uom', 'locations__capacity_uom'
    ).all()

    if search_query:
        items = items.filter(
            Q(name__icontains=search_query) | 
            Q(category__name__icontains=search_query) | 
            Q(code__icontains=search_query)
        )
    return render(request, 'products/list.html', {'items': items, 'search_query': search_query})

# -------------------------------------------------------
#   ADD PRODUCT
# -------------------------------------------------------
@login_required
@admin_required
def product_add(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product "{product.name}" created successfully.')
            return redirect('products:list')
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
        'title': 'Add New Product',
        'uoms_by_category': uoms_by_category,
    }
    return render(request, 'products/form.html', context)

# -------------------------------------------------------
#   UPDATE PRODUCT
# -------------------------------------------------------
@login_required
@admin_required
def product_update(request, pk):
    item = get_object_or_404(Product, id=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f'Product "{item.name}" updated successfully.')
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
        'title': f'Edit: {item.name}',
        'uoms_by_category': uoms_by_category,
    }
    return render(request, 'products/form.html', context)

# -------------------------------------------------------
#   DELETE PRODUCT
# -------------------------------------------------------
@login_required
@admin_required
def product_delete(request, pk):
    item = get_object_or_404(Product, id=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, f'Product "{item.name}" deleted.')
        return redirect('products:list')
    return render(request, 'products/confirm_delete.html', {'item': item})

# -------------------------------------------------------
#   PRODUCT DETAIL
# -------------------------------------------------------
@login_required
@admin_required
def product_detail(request, pk):
    product = get_object_or_404(Product.objects.prefetch_related(
        'locations__tray__shelf', 'locations__quantity_uom', 'locations__capacity_uom'
    ), pk=pk)
    
    order_history = Order.objects.filter(product=product).select_related(
        'staff', 'prescription__patient'
    ).order_by('-date')[:10]

    all_boms_list = list(BillOfMaterials.objects.filter(product=product).values(
        'product_id', 'uom_from_id', 'uom_to_id', 'conversion_factor'
    ))

    batches_data = []
    total_allocated_product = 0 
    all_batches = product.batches.all().order_by('expiry_date')

    for batch in all_batches:
        allocated_qty_batch = 0
        locations = batch.batch_locations.all().select_related('quantity_uom', 'tray__shelf')

        for loc in locations:
            factor = get_smart_conversion_factor(product.id, loc.quantity_uom_id, product.base_uom_id, all_boms_list)
            allocated_qty_batch += loc.quantity * factor
        
        allocated_qty_batch = round(allocated_qty_batch, 2)
        if allocated_qty_batch.is_integer(): allocated_qty_batch = int(allocated_qty_batch)

        unallocated_qty_batch = max(0, batch.quantity - allocated_qty_batch)
        total_allocated_product += allocated_qty_batch
        
        batches_data.append({
            'obj': batch,
            'allocated': allocated_qty_batch,
            'unallocated': unallocated_qty_batch,
            'locations': locations
        })

    total_unallocated_product = max(0, product.quantity - total_allocated_product)

    context = {
        'product': product, 
        'order_history': order_history,
        'batches_data': batches_data,
        'calculated_allocated': total_allocated_product,
        'calculated_unallocated': total_unallocated_product,
    }
    return render(request, 'products/detail.html', context)


# =======================================================
#               PRODUCT CATEGORY MANAGEMENT
# =======================================================

# -------------------------------------------------------
#   CATEGORY LIST
# -------------------------------------------------------
@login_required
@admin_required
def category_list(request):
    return render(request, 'product_category/list.html', {'categories': ProductCategory.objects.all()})

# -------------------------------------------------------
#   ADD/UPDATE CATEGORY
# -------------------------------------------------------
@login_required
@admin_required
def category_form(request, pk=None):
    instance = get_object_or_404(ProductCategory, pk=pk) if pk else None
    form = ProductCategoryForm(request.POST or None, instance=instance)
    
    if form.is_valid():
        form.save()
        messages.success(request, 'Category saved successfully.')
        return redirect('products:category_list')
        
    title = 'Edit Category' if instance else 'Create Category'
    return render(request, 'product_category/form.html', {'form': form, 'title': title})

# -------------------------------------------------------
#   CATEGORY DETAIL
# -------------------------------------------------------
@login_required
@admin_required
def category_detail(request, pk):
    category = get_object_or_404(ProductCategory.objects.prefetch_related('children', 'product_set'), pk=pk)
    return render(request, 'product_category/detail.html', {'category': category})

# -------------------------------------------------------
#   DELETE CATEGORY
# -------------------------------------------------------
@login_required
@admin_required
def category_delete(request, pk):
    category = get_object_or_404(ProductCategory, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, f'Category "{category.name}" deleted.')
        return redirect('products:category_list')
    return render(request, 'product_category/confirm_delete.html', {'item': category})


# =======================================================
#               UOM CATEGORY MANAGEMENT
# =======================================================

# -------------------------------------------------------
#   UOM CATEGORY LIST
# -------------------------------------------------------
@login_required
@admin_required
def uom_category_list(request):
    return render(request, 'uom_category/list.html', {'categories': UomCategory.objects.all().order_by('name')})

# -------------------------------------------------------
#   ADD/UPDATE UOM CATEGORY
# -------------------------------------------------------
@login_required
@admin_required
def uom_category_form(request, pk=None):
    instance = get_object_or_404(UomCategory, pk=pk) if pk else None
    form = UomCategoryForm(request.POST or None, instance=instance)
    
    if form.is_valid():
        form.save()
        messages.success(request, 'UoM Category saved.')
        return redirect('products:uom_category_list')
        
    title = 'Edit UoM Category' if instance else 'Create UoM Category'
    return render(request, 'uom_category/form.html', {'form': form, 'title': title})

# -------------------------------------------------------
#   UOM CATEGORY DETAIL
# -------------------------------------------------------
@login_required
@admin_required
def uom_category_detail(request, pk):
    category = get_object_or_404(UomCategory.objects.prefetch_related('uoms'), pk=pk)
    return render(request, 'uom_category/detail.html', {'category': category})

# -------------------------------------------------------
#   DELETE UOM CATEGORY
# -------------------------------------------------------
@login_required
@admin_required
def uom_category_delete(request, pk):
    category = get_object_or_404(UomCategory, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, f'UoM Category "{category.name}" deleted.')
        return redirect('products:uom_category_list')
    return render(request, 'uom_category/confirm_delete.html', {'item': category})


# =======================================================
#               UNIT OF MEASURE MANAGEMENT
# =======================================================

# -------------------------------------------------------
#   UOM LIST
# -------------------------------------------------------
@login_required
@admin_required
def uom_list(request):
    return render(request, 'uom/list.html', {'uoms': UnitOfMeasure.objects.all()})

# -------------------------------------------------------
#   ADD/UPDATE UOM
# -------------------------------------------------------
@login_required
@admin_required
def uom_form(request, pk=None):
    instance = get_object_or_404(UnitOfMeasure, pk=pk) if pk else None
    form = UnitOfMeasureForm(request.POST or None, instance=instance)
    
    if form.is_valid():
        form.save()
        messages.success(request, 'Unit of Measure saved.')
        return redirect('products:uom_list')
        
    title = 'Edit Unit' if instance else 'Create Unit'
    return render(request, 'uom/form.html', {'form': form, 'title': title})

# -------------------------------------------------------
#   UOM DETAIL
# -------------------------------------------------------
@login_required
@admin_required
def uom_detail(request, pk):
    uom = get_object_or_404(UnitOfMeasure.objects.select_related('category'), pk=pk)
    return render(request, 'uom/detail.html', {'uom': uom})

# -------------------------------------------------------
#   DELETE UOM
# -------------------------------------------------------
@login_required
@admin_required
def uom_delete(request, pk):
    uom = get_object_or_404(UnitOfMeasure, pk=pk)
    if request.method == 'POST':
        uom.delete()
        messages.success(request, f'Unit "{uom.name}" deleted.')
        return redirect('products:uom_list')
    return render(request, 'uom/confirm_delete.html', {'item': uom})


# =======================================================
#               BILL OF MATERIALS (BOM)
# =======================================================

# -------------------------------------------------------
#   BOM LIST
# -------------------------------------------------------
@login_required
@admin_required
def bom_list(request):
    boms = BillOfMaterials.objects.select_related('product', 'uom_from', 'uom_to').all().order_by('product__name')
    return render(request, 'bom/list.html', {'boms': boms})

# -------------------------------------------------------
#   ADD/UPDATE BOM
# -------------------------------------------------------
@login_required
@admin_required
def bom_form(request, pk=None):
    instance = get_object_or_404(BillOfMaterials, pk=pk) if pk else None
    form = BillOfMaterialsForm(request.POST or None, instance=instance)
    
    if form.is_valid():
        form.save()
        messages.success(request, 'Conversion rule saved.')
        return redirect('products:bom_list')
        
    title = 'Edit Rule' if instance else 'Create Rule'

    products_json = json.dumps(list(Product.objects.filter(uom_category__isnull=False).values('id', 'uom_category_id')))
    
    all_uoms = UnitOfMeasure.objects.values('id', 'name', 'category_id')
    uoms_map = {}
    for uom in all_uoms:
        if uom['category_id'] not in uoms_map: uoms_map[uom['category_id']] = []
        uoms_map[uom['category_id']].append({'id': uom['id'], 'name': uom['name']})

    context = {
        'form': form, 
        'title': title,
        'products_with_uom_cat_json': products_json,
        'uoms_by_category_json': json.dumps(uoms_map),
    }
    return render(request, 'bom/form.html', context)

# -------------------------------------------------------
#   BOM DETAIL
# -------------------------------------------------------
@login_required
@admin_required
def bom_detail(request, pk):
    bom = get_object_or_404(BillOfMaterials.objects.select_related('product', 'uom_from', 'uom_to'), pk=pk)
    return render(request, 'bom/detail.html', {'bom': bom})

# -------------------------------------------------------
#   DELETE BOM
# -------------------------------------------------------
@login_required
@admin_required
def bom_delete(request, pk):
    bom = get_object_or_404(BillOfMaterials, pk=pk)
    if request.method == 'POST':
        bom.delete()
        messages.success(request, 'Rule deleted.')
        return redirect('products:bom_list')
    return render(request, 'bom/confirm_delete.html', {'item': bom})


# =======================================================
#               API ENDPOINTS
# =======================================================

# -------------------------------------------------------
#   PRODUCT SEARCH API
# -------------------------------------------------------
@login_required
@admin_required
def product_search_api(request):
    query = request.GET.get('q', '')
    if len(query) >= 2:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(code__icontains=query) | Q(category__name__icontains=query)
        ).select_related('category', 'base_uom')[:10] 
        
        results = [{
            'id': p.id,
            'name': p.name,
            'code': p.code,
            'category': p.category.name if p.category else 'N/A',
            'quantity': p.quantity,
            'uom': p.base_uom.name if p.base_uom else 'N/A',
            'url': reverse('products:detail', args=[p.id])
        } for p in products]
    else:
        results = []
    return JsonResponse(results, safe=False)


# =======================================================
#               STOCK LOCATION MANAGEMENT
# =======================================================

# -------------------------------------------------------
#   MANAGE LOCATIONS VIEW
# -------------------------------------------------------
@login_required
@admin_required
def manage_locations(request):
    all_shelves = Shelf.objects.prefetch_related(
        'trays', 'trays__location__product', 'trays__location__batch', 
        'trays__location__quantity_uom', 'trays__location__capacity_uom'
    ).all()
    
    # Products & UoM Data
    all_products_data = list(Product.objects.values('id', 'name', 'code', 'quantity', 'uom_category_id', 'base_uom__name', 'base_uom_id'))
    
    all_uoms = UnitOfMeasure.objects.values('id', 'name', 'category_id')
    uoms_by_category = {}
    for uom in all_uoms:
        if uom['category_id'] not in uoms_by_category: uoms_by_category[uom['category_id']] = []
        uoms_by_category[uom['category_id']].append({'id': uom['id'], 'name': uom['name']})
    
    # Locations Data
    locations = StockLocation.objects.select_related('product', 'batch', 'quantity_uom', 'capacity_uom').all()
    all_locations_data = []
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
        })

    # BOM Data
    all_boms_data = list(BillOfMaterials.objects.values('product_id', 'uom_from_id', 'uom_to_id', 'conversion_factor'))
    safe_boms = [{'product_id': b['product_id'], 'uom_from_id': b['uom_from_id'], 'uom_to_id': b['uom_to_id'], 'conversion_factor': float(b['conversion_factor'])} for b in all_boms_data]

    context = {
        'all_shelves': all_shelves,
        'all_products_data': all_products_data,
        'uoms_by_category': uoms_by_category,
        'all_locations_data': all_locations_data,
        'all_boms_data': safe_boms,
    }
    return render(request, 'products/manage_locations.html', context)

# -------------------------------------------------------
#   API: GET BATCH DETAILS
# -------------------------------------------------------
@login_required
@admin_required
def api_get_product_batches_details(request):
    product_id = request.GET.get('product_id')
    if not product_id: return JsonResponse({'status': 'error', 'message': 'Missing product ID'})
    
    product = get_object_or_404(Product, pk=product_id)
    all_boms_list = list(BillOfMaterials.objects.filter(product=product).values('product_id', 'uom_from_id', 'uom_to_id', 'conversion_factor'))

    batches = product.batches.filter(quantity__gt=0).order_by('expiry_date')
    batches_data = []
    
    for batch in batches:
        allocated = 0
        for loc in batch.batch_locations.select_related('quantity_uom'):
            factor = get_smart_conversion_factor(product.id, loc.quantity_uom_id, product.base_uom_id, all_boms_list)
            allocated += loc.quantity * factor
            
        allocated = int(allocated) if round(allocated, 2).is_integer() else round(allocated, 2)
        unallocated = max(0, batch.quantity - allocated)

        batches_data.append({
            'id': batch.id,
            'batch_number': batch.batch_number,
            'expiry': batch.expiry_date.strftime('%d/%m/%Y'),
            'total': batch.quantity,
            'allocated': allocated,
            'unallocated': unallocated
        })

    return JsonResponse({
        'status': 'ok',
        'base_uom': product.base_uom.name if product.base_uom else '',
        'batches': batches_data
    })

# -------------------------------------------------------
#   API: SAVE LOCATION
# -------------------------------------------------------
@login_required
@admin_required
@require_POST
def api_save_location(request):
    try:
        data = json.loads(request.body)
        tray_id = data.get('tray_id')
        batch_id = data.get('batch_id')
        
        if not tray_id: return JsonResponse({'status': 'error', 'message': 'Missing Tray ID'}, status=400)

        with transaction.atomic():
            StockLocation.objects.filter(tray_id=tray_id).delete()
            
            if batch_id:
                batch = get_object_or_404(ProductBatch, pk=batch_id)
                StockLocation.objects.create(
                    tray_id=tray_id,
                    product=batch.product,
                    batch=batch,
                    quantity=int(data.get('quantity', 0)),
                    quantity_uom_id=data.get('quantity_uom_id'),
                    capacity=int(data.get('capacity', 50)),
                    capacity_uom_id=data.get('capacity_uom_id')
                )
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)