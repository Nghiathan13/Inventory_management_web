# =======================================================
#               KHAI BÁO THƯ VIỆN (IMPORTS)
# =======================================================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.http import JsonResponse
import json

# Models
from .models import Order, PurchaseOrder, PurchaseOrderDetail, StockReceipt
from doctor.models import Prescription, PrescriptionDetail
from products.models import Product, BillOfMaterials, ProductBatch
from carousel.models import Carousel, Shelf, StockLocation

# Decorators
from main.decorators import admin_required


# =======================================================
#        MODULE 1: PICKING PROCESS & CAROUSEL LOGIC
# =======================================================

@login_required
@admin_required
def api_calculate_picking_path(request, prescription_id):
    """
    Tính toán lộ trình lấy thuốc tối ưu (Split Picking + FEFO + Nearest Neighbor).
    """
    prescription = get_object_or_404(Prescription, pk=prescription_id)
    carousel = Carousel.objects.first()
    
    if not carousel:
        return JsonResponse({'status': 'error', 'message': 'Hệ thống kệ chưa được khởi tạo.'}, status=400)

    all_shelves = list(Shelf.objects.values_list('name', flat=True))
    picking_list = []

    for detail in prescription.details.all():
        if detail.is_collected: continue 

        product = detail.product
        qty_needed = detail.quantity 
        
        # Lấy vị trí có hàng (FEFO)
        locations = StockLocation.objects.filter(
            product=product, 
            quantity__gt=0
        ).select_related('batch', 'tray__shelf').order_by('batch__expiry_date')

        # --- Logic Tách Lô (Split Picking) ---
        for loc in locations:
            if qty_needed <= 0: break
            
            qty_available = loc.quantity
            qty_to_pick = min(qty_needed, qty_available)
            
            shelf_name = loc.tray.shelf.name
            shelf_index = all_shelves.index(shelf_name) if shelf_name in all_shelves else 0

            picking_list.append({
                'detail_id': detail.id,
                'product_id': product.id,
                'product_name': product.name,
                'required_qty': qty_to_pick,
                'stock_at_shelf': qty_available,
                'uom': detail.uom.name if detail.uom else product.base_uom.name,
                'location_id': loc.id,
                'tray_level': loc.tray.level,
                'shelf_name': shelf_name,
                'shelf_index': shelf_index,
                'batch_number': loc.batch.batch_number,
                'expiry_date': loc.batch.expiry_date.strftime('%d/%m/%Y'),
                'is_picked': False,
                'is_last_step': (qty_needed - qty_to_pick) <= 0
            })
            qty_needed -= qty_to_pick

    # --- Sắp xếp đường đi tối ưu (Nearest Neighbor) ---
    total_shelves = len(all_shelves)
    current_shelf_index = all_shelves.index(carousel.current_shelf_at_gate)
    sorted_picking_list = []
    curr_idx = current_shelf_index

    while picking_list:
        nearest_item = None
        min_dist = float('inf')
        
        for item in picking_list:
            target_idx = item['shelf_index']
            dist_cw = (target_idx - curr_idx + total_shelves) % total_shelves
            dist_ccw = (curr_idx - target_idx + total_shelves) % total_shelves
            dist = min(dist_cw, dist_ccw)
            
            if dist < min_dist:
                min_dist = dist
                nearest_item = item
        
        sorted_picking_list.append(nearest_item)
        picking_list.remove(nearest_item)
        curr_idx = nearest_item['shelf_index']

    return JsonResponse({
        'status': 'ok',
        'path': sorted_picking_list,
        'current_shelf': carousel.current_shelf_at_gate
    })


@login_required
@admin_required
@require_POST
@transaction.atomic
def api_confirm_pick(request):
    """
    Xác nhận lấy thuốc tại một vị trí kệ:
    1. Trừ kho kệ (StockLocation).
    2. Trừ kho lô (ProductBatch).
    3. Cập nhật trạng thái chi tiết đơn thuốc (PrescriptionDetail).
    """
    try:
        data = json.loads(request.body)
        location_id = data.get('location_id')
        qty_picked = int(data.get('quantity'))
        detail_id = data.get('detail_id')
        
        # 1. Trừ kho kệ
        loc = StockLocation.objects.select_related('batch').get(id=location_id)
        if loc.quantity < qty_picked:
             return JsonResponse({'status': 'error', 'message': 'Không đủ tồn kho trên kệ.'}, status=400)
        
        loc.quantity -= qty_picked
        loc.save()

        # 2. Trừ kho Lô (Signal sẽ tự update Product tổng)
        batch = loc.batch
        batch.quantity = F('quantity') - qty_picked
        batch.save()
        
        # 3. Đánh dấu detail là đã lấy (để tránh trừ 2 lần khi Complete)
        if detail_id:
            detail = PrescriptionDetail.objects.get(id=detail_id)
            detail.is_collected = True 
            detail.save()

        return JsonResponse({'status': 'ok', 'message': f'Đã lấy {qty_picked} sản phẩm.'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@admin_required
@require_POST
@transaction.atomic
def api_undo_pick(request):
    """
    Hoàn tác lấy thuốc (Trả lại kho nếu lỡ ấn nhầm).
    """
    try:
        data = json.loads(request.body)
        location_id = data.get('location_id')
        qty_picked = int(data.get('quantity'))
        
        loc = StockLocation.objects.get(id=location_id)
        
        # Cộng lại kho kệ và lô
        loc.quantity = F('quantity') + qty_picked
        loc.save()
        
        batch = loc.batch
        batch.quantity = F('quantity') + qty_picked
        batch.save()

        return JsonResponse({'status': 'ok', 'message': 'Đã hoàn tác.'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# =======================================================
#        MODULE 2: DISPENSE (XUẤT KHO / CẤP PHÁT)
# =======================================================

@login_required
@admin_required
def dispense_list(request):
    """Hiển thị danh sách toa thuốc đang chờ (Pending)."""
    pending_prescriptions = Prescription.objects.filter(status='Pending').select_related('patient', 'doctor').order_by('created_at')
    return render(request, 'dispense/list.html', {'pending_prescriptions': pending_prescriptions})


@login_required
@admin_required
def dispense_process(request, pk):
    """
    Xử lý hoàn tất đơn thuốc.
    Lưu ý: Việc trừ kho đã được thực hiện bởi API Confirm Pick.
    Hàm này chỉ chốt đơn và ghi lịch sử.
    """
    try:
        prescription = Prescription.objects.get(id=pk, status='Pending')
    except Prescription.DoesNotExist:
        messages.warning(request, 'Toa thuốc này đã được xử lý hoặc không tồn tại.')
        return redirect('inventory:dispense_list')

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Duyệt qua các chi tiết để ghi log và xử lý các mục chưa pick (nếu có)
                for detail in prescription.details.all():
                    
                    # Nếu chưa pick bằng tool (thủ công), trừ kho tại đây
                    if not detail.is_collected:
                        product = detail.product
                        quantity_to_deduct = detail.quantity
                        
                        if product.quantity < quantity_to_deduct:
                            raise Exception(f"Không đủ tồn kho cho '{product.name}'. Vui lòng dùng Picking Assistant.")
                        
                        # Trừ kho tổng (nếu chưa dùng batch picking)
                        # Lưu ý: Nếu dùng hệ thống batch bắt buộc, nên chặn ở đây
                        product.quantity -= quantity_to_deduct
                        product.save()
                        
                        detail.is_collected = True
                        detail.save()

                    # Ghi lịch sử xuất kho (Order History)
                    if not Order.objects.filter(prescription=prescription, product=detail.product).exists():
                        Order.objects.create(
                            prescription=prescription,
                            product=detail.product,
                            order_quantity=detail.quantity,
                            staff=request.user
                        )
                
                # Cập nhật trạng thái Toa -> Dispensed
                prescription.status = 'Dispensed'
                prescription.completed_at = timezone.now()
                prescription.save()
                
                messages.success(request, f'Đã hoàn thành cấp phát toa #{prescription.id}.')
                return redirect('inventory:dispense_list')

        except Exception as e:
            messages.error(request, f'Lỗi khi hoàn tất: {e}')
            return render(request, 'dispense/process.html', {'prescription': prescription})

    return render(request, 'dispense/process.html', {'prescription': prescription})


# =======================================================
#        MODULE 3: PURCHASING (ĐẶT HÀNG NCC)
# =======================================================

@login_required
@admin_required
def reorder_list(request):
    """Danh sách sản phẩm dưới định mức cần đặt hàng."""
    products_to_reorder = Product.objects.filter(
        quantity__lte=F('reorder_point'),
        supplier__isnull=False
    ).exclude(supplier__exact='')
    
    purchase_orders = PurchaseOrder.objects.all().order_by('-created_at')
    supplier_users = User.objects.filter(groups__name='Supplier')

    context = {
        'products_to_reorder': products_to_reorder,
        'suppliers': supplier_users,
        'purchase_orders': purchase_orders,
    }
    return render(request, 'purchasing/reorder_list.html', context)


@login_required
@admin_required
def create_purchase_order(request):
    """Tạo đơn đặt hàng mới gửi NCC."""
    if request.method == 'POST':
        product_ids = request.POST.getlist('products_to_order')
        supplier_id = request.POST.get('supplier_id')
        
        if not product_ids or not supplier_id:
            messages.error(request, "Vui lòng chọn nhà cung cấp và sản phẩm.")
            return redirect('inventory:reorder_list')
        
        supplier = get_object_or_404(User, id=supplier_id)
        products = Product.objects.filter(id__in=product_ids)
        
        new_po = PurchaseOrder.objects.create(supplier=supplier, created_by=request.user, status='To Confirm')

        for product in products:
            quantity_to_order = request.POST.get(f'quantity_{product.id}', product.reorder_point * 2)
            PurchaseOrderDetail.objects.create(
                purchase_order=new_po,
                product=product,
                quantity=int(quantity_to_order)
            )

        messages.success(request, f'Đã tạo PO #{new_po.id} gửi đến {supplier.username}.')
        return redirect('inventory:reorder_list')
    return redirect('inventory:reorder_list')


@login_required
@admin_required
def purchase_order_detail(request, pk):
    """Xem chi tiết đơn đặt hàng."""
    po = get_object_or_404(PurchaseOrder.objects.prefetch_related('details__product'), pk=pk)
    return render(request, 'purchasing/po_detail.html', {'po': po})


# =======================================================
#        MODULE 4: STOCK IN (NHẬP KHO)
# =======================================================

@login_required
@admin_required
def stock_in_scan(request):
    """Giao diện quét QR nhập kho."""
    return render(request, 'stock_in/scan.html')


@login_required
@admin_required
def receive_purchase_order(request, po_code):
    """Giao diện nhận đơn hàng sau khi quét mã tổng."""
    po = get_object_or_404(PurchaseOrder.objects.prefetch_related('details__product'), unique_code=po_code)

    if po.status != 'Confirmed':
        msg_type = messages.WARNING if po.status == 'Received' else messages.ERROR
        messages.add_message(request, msg_type, f"Đơn hàng #{po.id} có trạng thái '{po.get_status_display}'.")
        return redirect('inventory:stock_in_scan')
    
    detail_codes = {
        str(detail.unique_code).lower(): {
            'product_name': detail.product.name,
            'quantity': detail.quantity
        } for detail in po.details.all()
    }

    return render(request, 'stock_in/receive_po.html', {'po': po, 'detail_codes_data': detail_codes})


@login_required
@admin_required
@transaction.atomic
def stock_in_process_api(request, detail_code):
    """API xử lý nhập kho từng sản phẩm (khi quét mã con)."""
    if request.method == 'POST':
        po_detail = get_object_or_404(PurchaseOrderDetail, unique_code=detail_code)
        
        if StockReceipt.objects.filter(from_po_detail=po_detail).exists():
            return JsonResponse({'status': 'warning', 'message': f'Sản phẩm "{po_detail.product.name}" đã quét trước đó.'})

        product = po_detail.product
        
        # 1. Tạo/Cập nhật Lô (Batch)
        # Signal (models.py) sẽ tự động cập nhật Product.quantity
        batch_num = f"BATCH-{po_detail.expiry_date.strftime('%Y%m%d')}-{po_detail.id}"
        
        batch, created = ProductBatch.objects.get_or_create(
            product=product,
            expiry_date=po_detail.expiry_date,
            batch_number=batch_num,
            defaults={'quantity': 0}
        )
        
        batch.quantity = F('quantity') + po_detail.quantity
        batch.save()
        
        # 2. Ghi lịch sử
        StockReceipt.objects.create(
            product=product,
            quantity_received=po_detail.quantity,
            expiry_date=po_detail.expiry_date,
            received_by=request.user,
            from_po_detail=po_detail
        )
        
        # 3. Kiểm tra hoàn tất đơn hàng
        po = po_detail.purchase_order
        received_cnt = StockReceipt.objects.filter(from_po_detail__purchase_order=po).count()
        total_cnt = po.details.count()
        
        is_fully = False
        if received_cnt == total_cnt:
            po.status = 'Received'
            po.received_at = timezone.now()
            po.save()
            is_fully = True

        return JsonResponse({
            'status': 'success', 
            'message': f'Đã nhập {po_detail.quantity} {product.name} vào Lô {batch.batch_number}',
            'is_fully_received': is_fully
        })

    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)


# =======================================================
#        MODULE 5: MANUAL RECEIVE & HISTORY
# =======================================================

@login_required
@admin_required
def manual_receive_list(request):
    confirmed_pos = PurchaseOrder.objects.filter(status='Confirmed').order_by('confirmed_at')
    return render(request, 'manual_receive/list.html', {'purchase_orders': confirmed_pos})


@login_required
@admin_required
def manual_receive_order(request, po_pk):
    po = get_object_or_404(PurchaseOrder.objects.prefetch_related('details__product', 'details__stockreceipt'), pk=po_pk)
    all_received = all(hasattr(detail, 'stockreceipt') for detail in po.details.all())
    return render(request, 'manual_receive/detail.html', {'po': po, 'all_received': all_received})


@login_required
@admin_required
@transaction.atomic
def manual_update_item(request, detail_pk):
    """Xử lý nhập kho thủ công (không dùng QR)."""
    if request.method == 'POST':
        po_detail = get_object_or_404(PurchaseOrderDetail, pk=detail_pk)

        if hasattr(po_detail, 'stockreceipt'):
            messages.warning(request, 'Sản phẩm này đã được nhập kho.')
        else:
            product = po_detail.product
            
            # Tạo batch mặc định (hoặc lấy batch hiện có nếu chưa hỗ trợ nhập date thủ công)
            # Ở đây giả định logic đơn giản: cộng vào kho tổng
            product.quantity = F('quantity') + po_detail.quantity
            product.save()
            
            StockReceipt.objects.create(
                product=product,
                quantity_received=po_detail.quantity,
                received_by=request.user,
                from_po_detail=po_detail
            )
            messages.success(request, f'Đã nhập kho: {product.name}')

        return redirect('inventory:manual_receive_order', po_pk=po_detail.purchase_order.pk)
    
    return redirect('inventory:manual_receive_list')


@login_required
@admin_required
def order_history(request):
    orders = Order.objects.all().order_by('-date')
    return render(request, 'order_history/order_history.html', {'orders': orders})