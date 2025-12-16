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
import logging

# Models
from .models import Order, PurchaseOrder, PurchaseOrderDetail, StockReceipt
from doctor.models import Prescription, PrescriptionDetail
from products.models import Product, ProductBatch, BillOfMaterials
from carousel.models import Carousel, Shelf, StockLocation

# Decorators
from main.decorators import admin_required

logger = logging.getLogger(__name__)

# =======================================================
#        HELPER: THUẬT TOÁN QUY ĐỔI BOM (BFS)
#        (Copy từ products/views.py để dùng chung)
# =======================================================
def get_conversion_factor(product_id, from_uom_id, to_uom_id, all_boms_list=None):
    """
    Tìm hệ số nhân để đổi từ 'from_uom' sang 'to_uom'.
    Ví dụ: Hộp -> Viên (Factor = 100).
    """
    if not from_uom_id or not to_uom_id: return 1.0
    if from_uom_id == to_uom_id: return 1.0

    # Nếu chưa có list BOM thì query lấy
    if all_boms_list is None:
        all_boms_list = list(BillOfMaterials.objects.filter(product_id=product_id).values(
            'product_id', 'uom_from_id', 'uom_to_id', 'conversion_factor'
        ))

    # 1. Xây dựng đồ thị 2 chiều
    graph = {}
    for bom in all_boms_list:
        # Cạnh xuôi: A -> B (factor)
        if bom['uom_from_id'] not in graph: graph[bom['uom_from_id']] = []
        graph[bom['uom_from_id']].append({'to': bom['uom_to_id'], 'factor': float(bom['conversion_factor'])})
        
        # Cạnh ngược: B -> A (1 / factor)
        if bom['uom_to_id'] not in graph: graph[bom['uom_to_id']] = []
        try:
            reverse_factor = 1.0 / float(bom['conversion_factor'])
        except ZeroDivisionError:
            reverse_factor = 0
        graph[bom['uom_to_id']].append({'to': bom['uom_from_id'], 'factor': reverse_factor})

    # 2. BFS tìm đường đi ngắn nhất
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
    
    # Không tìm thấy đường quy đổi -> Mặc định 1 (tránh crash)
    return 1.0


# =======================================================
#           PICKING PROCESS & CAROUSEL LOGIC
# =======================================================

#--------------------------------------------------------
#       TÍNH TOÁN LỘ TRÌNH (FEFO + NEAREST NEIGHBOR)
#--------------------------------------------------------
@login_required
@admin_required
def api_calculate_picking_path(request, prescription_id):
    prescription = get_object_or_404(Prescription, pk=prescription_id)
    carousel = Carousel.objects.first()
    
    if not carousel:
        return JsonResponse({'status': 'error', 'message': 'Hệ thống kệ chưa được khởi tạo.'}, status=400)

    # Lấy danh sách kệ để sắp xếp (A, B, C...)
    all_shelves = list(Shelf.objects.values_list('name', flat=True))
    
    # Lấy toàn bộ BOM một lần để tối ưu Query
    all_boms_list = list(BillOfMaterials.objects.values('product_id', 'uom_from_id', 'uom_to_id', 'conversion_factor'))
    
    picking_list = []

    # --- DUYỆT TỪNG CHI TIẾT TRONG TOA ---
    for detail in prescription.details.all():
        if detail.is_collected: continue 

        try:
            product = detail.product
            base_uom_id = product.base_uom.id
            
            # 1. Đơn vị yêu cầu trong toa (VD: Hộp)
            req_uom_id = detail.uom.id if detail.uom else base_uom_id
            req_uom_name = detail.uom.name if detail.uom else product.base_uom.name
            
            # 2. Tính tổng nhu cầu ra Đơn vị cơ bản (VD: 1 Hộp = 100 Viên)
            # Dùng filter list BOM theo product_id để tránh lẫn lộn
            product_boms = [b for b in all_boms_list if b['product_id'] == product.id]
            
            factor_req_to_base = get_conversion_factor(product.id, req_uom_id, base_uom_id, product_boms)
            qty_needed_base = float(detail.quantity) * factor_req_to_base
            
            # 3. Tìm các vị trí có hàng (FEFO - Hết hạn trước ra trước)
            locations = StockLocation.objects.filter(
                product=product, 
                quantity__gt=0
            ).select_related('batch', 'tray__shelf', 'quantity_uom').order_by('batch__expiry_date')

            if not locations.exists():
                # Nếu không có hàng, bỏ qua hoặc báo lỗi (ở đây ta bỏ qua để chạy tiếp thuốc sau)
                continue

            for loc in locations:
                # Nếu đã lấy đủ thì dừng tìm vị trí cho thuốc này
                if qty_needed_base <= 0.001: break 
                
                # Quy đổi tồn kho trên kệ ra Base Unit
                loc_uom_id = loc.quantity_uom.id if loc.quantity_uom else base_uom_id
                loc_uom_name = loc.quantity_uom.name if loc.quantity_uom else product.base_uom.name
                
                factor_loc_to_base = get_conversion_factor(product.id, loc_uom_id, base_uom_id, product_boms)
                qty_available_base = float(loc.quantity) * factor_loc_to_base
                
                # Quyết định lấy bao nhiêu (tính theo Base Unit)
                # Lấy Min giữa "Cần" và "Có"
                qty_pick_base = min(qty_needed_base, qty_available_base)
                
                # --- LOGIC HIỂN THỊ THÔNG MINH (TRÁNH SỐ LẺ) ---
                # Thử quy đổi ngược về Đơn vị yêu cầu (Hộp)
                if factor_req_to_base > 0:
                    qty_pick_display = qty_pick_base / factor_req_to_base
                else:
                    qty_pick_display = qty_pick_base

                display_uom_name = req_uom_name
                display_uom_id = req_uom_id

                # Nếu ra số lẻ (VD: 0.2 Hộp), chuyển sang hiển thị Base Unit (Viên)
                if not float(qty_pick_display).is_integer():
                    qty_pick_display = qty_pick_base # Dùng số Viên
                    display_uom_name = product.base_uom.name
                    display_uom_id = base_uom_id
                    
                    # Làm tròn đẹp
                    if qty_pick_display.is_integer():
                        qty_pick_display = int(qty_pick_display)
                    else:
                        qty_pick_display = round(qty_pick_display, 2)
                else:
                    qty_pick_display = int(qty_pick_display)
                # ------------------------------------------------

                shelf_name = loc.tray.shelf.name
                try:
                    shelf_index = all_shelves.index(shelf_name)
                except ValueError:
                    shelf_index = 0

                picking_list.append({
                    'detail_id': detail.id,
                    'product_id': product.id,
                    'product_name': product.name,
                    
                    # Dữ liệu hiển thị & Confirm
                    'required_qty': qty_pick_display, 
                    'uom': display_uom_name,
                    'uom_id': display_uom_id, # ID đơn vị hiển thị (quan trọng để confirm)
                    
                    'stock_at_shelf': loc.quantity,
                    'shelf_uom': loc_uom_name, 

                    'location_id': loc.id,
                    'tray_level': loc.tray.level,
                    'shelf_name': shelf_name,
                    'shelf_index': shelf_index,
                    'batch_number': loc.batch.batch_number if loc.batch else "N/A",
                    'expiry_date': loc.batch.expiry_date.strftime('%d/%m/%Y') if loc.batch else "N/A",
                    'is_picked': False,
                })
                
                # Trừ đi lượng đã lấy được
                qty_needed_base -= qty_pick_base
            
            # Đánh dấu bước cuối cùng của thuốc này
            if picking_list:
                if qty_needed_base <= 0.001:
                    picking_list[-1]['is_last_step'] = True
                else:
                    # Nếu chạy hết location mà vẫn thiếu hàng
                    picking_list[-1]['is_last_step'] = False

        except Exception as e:
            # [QUAN TRỌNG] Nếu thuốc này lỗi, log lại và TIẾP TỤC thuốc sau
            # Không được để crash cả API
            print(f"Error processing detail {detail.id}: {e}")
            continue

    # 4. Sắp xếp đường đi tối ưu (Nearest Neighbor)
    if picking_list:
        total_shelves = len(all_shelves) if all_shelves else 1
        try:
            current_shelf_index = all_shelves.index(carousel.current_shelf_at_gate)
        except ValueError:
            current_shelf_index = 0
            
        sorted_picking_list = []
        curr_idx = current_shelf_index
        temp_list = list(picking_list)

        while temp_list:
            nearest_item = None
            min_dist = float('inf')
            for item in temp_list:
                target_idx = item['shelf_index']
                # Tính khoảng cách vòng tròn (ngắn nhất giữa xuôi và ngược)
                dist_cw = (target_idx - curr_idx + total_shelves) % total_shelves
                dist_ccw = (curr_idx - target_idx + total_shelves) % total_shelves
                dist = min(dist_cw, dist_ccw)
                
                if dist < min_dist:
                    min_dist = dist
                    nearest_item = item
            
            sorted_picking_list.append(nearest_item)
            temp_list.remove(nearest_item)
            curr_idx = nearest_item['shelf_index']
        
        picking_list = sorted_picking_list

    return JsonResponse({
        'status': 'ok',
        'path': picking_list,
        'current_shelf': carousel.current_shelf_at_gate
    })


#--------------------------------------------------------
#                   XÁC NHẬN LẤY HÀNG
#--------------------------------------------------------
@login_required
@admin_required
@require_POST
@transaction.atomic
def api_confirm_pick(request):
    try:
        data = json.loads(request.body)
        location_id = data.get('location_id')
        qty_picked = float(data.get('quantity')) # Số lượng user confirm (VD: 80)
        uom_id_picked = data.get('uom_id')       # Đơn vị user confirm (VD: ID của Viên)
        
        loc = StockLocation.objects.select_related('product', 'batch').get(id=location_id)
        product = loc.product
        
        base_uom_id = product.base_uom.id
        shelf_uom_id = loc.quantity_uom.id if loc.quantity_uom else base_uom_id

        if not uom_id_picked: uom_id_picked = base_uom_id

        # 1. Trừ kho trên Kệ (Quy đổi: UoM Pick -> UoM Kệ)
        # VD: Pick 80 Viên -> Kệ lưu Viên -> Factor = 1 -> Trừ 80
        factor_shelf = get_conversion_factor(product.id, uom_id_picked, shelf_uom_id)
        qty_deduct_shelf = qty_picked * factor_shelf
        
        # Cho phép sai số nhỏ float (0.01)
        if loc.quantity < (qty_deduct_shelf - 0.01):
             return JsonResponse({
                 'status': 'error', 
                 'message': f'Không đủ hàng trên kệ. Cần {qty_deduct_shelf}, có {loc.quantity}. (Vui lòng kiểm tra lại đơn vị tính)'
             }, status=400)
        
        loc.quantity -= qty_deduct_shelf
        if loc.quantity < 0: loc.quantity = 0
        loc.save()

        # 2. Trừ kho Lô (Quy đổi: UoM Pick -> Base UoM)
        factor_base = get_conversion_factor(product.id, uom_id_picked, base_uom_id)
        qty_deduct_batch = qty_picked * factor_base
        
        if loc.batch:
            loc.batch.quantity = F('quantity') - qty_deduct_batch
            loc.batch.save()
        
        # Trừ tổng kho Product (nếu có field quantity)
        if hasattr(product, 'quantity'):
             product.quantity = F('quantity') - qty_deduct_batch
             product.save()
        
        return JsonResponse({'status': 'ok', 'message': 'Đã trừ kho thành công.'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    
#--------------------------------------------------------
#                   HOÀN TÁC LẤY HÀNG
#--------------------------------------------------------
@login_required
@admin_required
@require_POST
@transaction.atomic
def api_undo_pick(request):
    try:
        data = json.loads(request.body)
        location_id = data.get('location_id')
        qty_picked = float(data.get('quantity'))
        detail_id = data.get('detail_id')
        
        loc = StockLocation.objects.get(id=location_id)
        product = loc.product

        # Lấy lại hệ số quy đổi
        prescription_uom_id = product.base_uom.id
        if detail_id:
            detail = PrescriptionDetail.objects.get(id=detail_id)
            if detail.uom: prescription_uom_id = detail.uom.id

        shelf_uom_id = loc.quantity_uom.id if loc.quantity_uom else product.base_uom.id
        base_uom_id = product.base_uom.id

        # Quy đổi
        factor_shelf = get_conversion_factor(product.id, prescription_uom_id, shelf_uom_id)
        factor_base = get_conversion_factor(product.id, prescription_uom_id, base_uom_id)
        
        # Cộng lại
        loc.quantity = F('quantity') + (qty_picked * factor_shelf)
        loc.save()
        
        batch = loc.batch
        batch.quantity = F('quantity') + (qty_picked * factor_base)
        batch.save()

        return JsonResponse({'status': 'ok', 'message': 'Đã hoàn tác.'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    

# =======================================================
#           DISPENSE (XUẤT KHO / CẤP PHÁT)
# =======================================================

#--------------------------------------------------------
#                   DANH SÁCH CHỜ CẤP PHÁT
#--------------------------------------------------------
@login_required
@admin_required
def dispense_list(request):
    pending_prescriptions = Prescription.objects.filter(status='Pending').select_related('patient', 'doctor').order_by('created_at')
    return render(request, 'dispense/list.html', {'pending_prescriptions': pending_prescriptions})


#--------------------------------------------------------
#                   XỬ LÝ HOÀN TẤT ĐƠN
#--------------------------------------------------------
@login_required
@admin_required
def dispense_process(request, pk):
    try:
        prescription = Prescription.objects.get(id=pk, status='Pending')
    except Prescription.DoesNotExist:
        messages.warning(request, 'Prescription not found or already processed.')
        return redirect('inventory:dispense_list')

    if request.method == 'POST':
        try:
            with transaction.atomic():
                for detail in prescription.details.all():
                    
                    # Trừ kho thủ công (nếu chưa qua Picking Tool)
                    if not detail.is_collected:
                        product = detail.product
                        quantity_to_deduct = detail.quantity
                        
                        if product.quantity < quantity_to_deduct:
                            raise Exception(f"Insufficient stock for '{product.name}'. Please use Picking Assistant.")
                        
                        product.quantity -= quantity_to_deduct
                        product.save()
                        
                        detail.is_collected = True
                        detail.save()

                    # Ghi log lịch sử
                    if not Order.objects.filter(prescription=prescription, product=detail.product).exists():
                        Order.objects.create(
                            prescription=prescription,
                            product=detail.product,
                            order_quantity=detail.quantity,
                            staff=request.user
                        )
                
                # Cập nhật trạng thái
                prescription.status = 'Dispensed'
                prescription.completed_at = timezone.now()
                prescription.save()
                
                messages.success(request, f'Prescription #{prescription.id} dispensed successfully.')
                return redirect('inventory:dispense_list')

        except Exception as e:
            messages.error(request, f'Error: {e}')
            return render(request, 'dispense/process.html', {'prescription': prescription})

    return render(request, 'dispense/process.html', {'prescription': prescription})


# =======================================================
#             MUA HÀNG (PURCHASING)
# =======================================================

#--------------------------------------------------------
#              DANH SÁCH CẦN ĐẶT HÀNG
#--------------------------------------------------------
@login_required
@admin_required
def reorder_list(request):
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


#--------------------------------------------------------
#              TẠO ĐƠN ĐẶT HÀNG (PO)
#--------------------------------------------------------
@login_required
@admin_required
def create_purchase_order(request):
    if request.method == 'POST':
        product_ids = request.POST.getlist('products_to_order')
        supplier_id = request.POST.get('supplier_id')
        
        if not product_ids or not supplier_id:
            messages.error(request, "Please select a supplier and products.")
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

        messages.success(request, f'PO #{new_po.id} created for {supplier.username}.')
        return redirect('inventory:reorder_list')
    return redirect('inventory:reorder_list')


#--------------------------------------------------------
#              CHI TIẾT ĐƠN ĐẶT HÀNG
#--------------------------------------------------------
@login_required
@admin_required
def purchase_order_detail(request, pk):
    po = get_object_or_404(PurchaseOrder.objects.prefetch_related('details__product'), pk=pk)
    return render(request, 'purchasing/po_detail.html', {'po': po})


# =======================================================
#                NHẬP KHO (STOCK IN)
# =======================================================

#--------------------------------------------------------
#               GIAO DIỆN QUÉT QR
#--------------------------------------------------------
@login_required
@admin_required
def stock_in_scan(request):
    return render(request, 'stock_in/scan.html')


#--------------------------------------------------------
#               NHẬN ĐƠN TỪ QR
#--------------------------------------------------------
@login_required
@admin_required
def receive_purchase_order(request, po_code):
    po = get_object_or_404(PurchaseOrder.objects.prefetch_related('details__product'), unique_code=po_code)

    if po.status != 'Confirmed':
        msg_type = messages.WARNING if po.status == 'Received' else messages.ERROR
        messages.add_message(request, msg_type, f"PO #{po.id} status is '{po.get_status_display}'.")
        return redirect('inventory:stock_in_scan')
    
    detail_codes = {
        str(detail.unique_code).lower(): {
            'product_name': detail.product.name,
            'quantity': detail.quantity
        } for detail in po.details.all()
    }

    return render(request, 'stock_in/receive_po.html', {'po': po, 'detail_codes_data': detail_codes})


#--------------------------------------------------------
#               API XỬ LÝ NHẬP KHO TỪNG MÓN
#--------------------------------------------------------
@login_required
@admin_required
@transaction.atomic
def stock_in_process_api(request, detail_code):
    if request.method == 'POST':
        po_detail = get_object_or_404(PurchaseOrderDetail, unique_code=detail_code)
        
        if StockReceipt.objects.filter(from_po_detail=po_detail).exists():
            return JsonResponse({'status': 'warning', 'message': f'Product "{po_detail.product.name}" already scanned.'})

        product = po_detail.product
        
        # Tạo Batch mới
        batch_num = f"BATCH-{po_detail.expiry_date.strftime('%Y%m%d')}-{po_detail.id}"
        batch, created = ProductBatch.objects.get_or_create(
            product=product,
            expiry_date=po_detail.expiry_date,
            batch_number=batch_num,
            defaults={'quantity': 0}
        )
        
        batch.quantity = F('quantity') + po_detail.quantity
        batch.save()
        
        # Ghi lịch sử
        StockReceipt.objects.create(
            product=product,
            quantity_received=po_detail.quantity,
            expiry_date=po_detail.expiry_date,
            received_by=request.user,
            from_po_detail=po_detail
        )
        
        # Kiểm tra hoàn tất
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
            'message': f'Received {po_detail.quantity} {product.name} into Batch {batch.batch_number}',
            'is_fully_received': is_fully
        })

    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)


# =======================================================
#         NHẬP KHO THỦ CÔNG & LỊCH SỬ 
# =======================================================

#--------------------------------------------------------
#            DANH SÁCH PO CẦN NHẬP (THỦ CÔNG)
#--------------------------------------------------------
@login_required
@admin_required
def manual_receive_list(request):
    confirmed_pos = PurchaseOrder.objects.filter(status='Confirmed').order_by('confirmed_at')
    return render(request, 'manual_receive/list.html', {'purchase_orders': confirmed_pos})


#--------------------------------------------------------
#            CHI TIẾT NHẬP KHO THỦ CÔNG
#--------------------------------------------------------
@login_required
@admin_required
def manual_receive_order(request, po_pk):
    po = get_object_or_404(PurchaseOrder.objects.prefetch_related('details__product', 'details__stockreceipt'), pk=po_pk)
    all_received = all(hasattr(detail, 'stockreceipt') for detail in po.details.all())
    return render(request, 'manual_receive/detail.html', {'po': po, 'all_received': all_received})


#--------------------------------------------------------
#                XỬ LÝ NHẬP KHO THỦ CÔNG
#--------------------------------------------------------
@login_required
@admin_required
@transaction.atomic
def manual_update_item(request, detail_pk):
    if request.method == 'POST':
        po_detail = get_object_or_404(PurchaseOrderDetail, pk=detail_pk)

        if hasattr(po_detail, 'stockreceipt'):
            messages.warning(request, 'Item already received.')
        else:
            product = po_detail.product
            product.quantity = F('quantity') + po_detail.quantity
            product.save()
            
            StockReceipt.objects.create(
                product=product,
                quantity_received=po_detail.quantity,
                received_by=request.user,
                from_po_detail=po_detail
            )
            messages.success(request, f'Stocked in: {product.name}')

        return redirect('inventory:manual_receive_order', po_pk=po_detail.purchase_order.pk)
    
    return redirect('inventory:manual_receive_list')


#--------------------------------------------------------
#                LỊCH SỬ XUẤT NHẬP
#--------------------------------------------------------
@login_required
@admin_required
def order_history(request):
    orders = Order.objects.all().order_by('-date')
    return render(request, 'order_history/order_history.html', {'orders': orders})