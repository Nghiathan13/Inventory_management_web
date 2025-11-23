import logging
import threading
import time

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Prefetch

from products.models import BillOfMaterials
from .models import Carousel, Shelf, Tray, StockLocation
from main.decorators import admin_required

logger = logging.getLogger(__name__)



# =======================================================
#        HELPER: THUẬT TOÁN QUY ĐỔI BOM (BFS)
# =======================================================
def get_conversion_factor(product_id, from_uom_id, to_uom_id, all_boms_list):
    """
    Tìm hệ số quy đổi giữa 2 đơn vị bằng thuật toán tìm đường (BFS).
    Sử dụng danh sách BOM đã fetch sẵn để tối ưu hiệu suất.
    """
    if not from_uom_id or not to_uom_id: return 1
    if from_uom_id == to_uom_id: return 1

    # 1. Xây dựng đồ thị cho sản phẩm này
    graph = {}
    # Lọc các rule liên quan đến product_id này từ list chung
    relevant_boms = [b for b in all_boms_list if b['product_id'] == product_id]

    for bom in relevant_boms:
        # Xuôi
        if bom['uom_from_id'] not in graph: graph[bom['uom_from_id']] = []
        graph[bom['uom_from_id']].append({'to': bom['uom_to_id'], 'factor': float(bom['conversion_factor'])})
        # Ngược
        if bom['uom_to_id'] not in graph: graph[bom['uom_to_id']] = []
        graph[bom['uom_to_id']].append({'to': bom['uom_from_id'], 'factor': 1.0 / float(bom['conversion_factor'])})

    # 2. BFS tìm đường
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
#               VIEW: HIỂN THỊ GIAO DIỆN
# =======================================================
@login_required
@admin_required
def control_panel(request):
    carousel = Carousel.objects.first()
    if not carousel:
        return render(request, 'carousel/initial_setup_required.html')
        
    # Fetch dữ liệu tối ưu
    shelves = Shelf.objects.prefetch_related(
        'trays__location__product',
        'trays__location__batch',
        'trays__location__quantity_uom',
        'trays__location__capacity_uom'
    ).all()

    # Lấy toàn bộ BOM một lần để dùng cho thuật toán (tránh query trong vòng lặp)
    all_boms_list = list(BillOfMaterials.objects.values(
        'product_id', 'uom_from_id', 'uom_to_id', 'conversion_factor'
    ))

    shelf_data = []
    for shelf in shelves:
        trays_info = []
        for tray in shelf.trays.all():
            product_obj = None
            batch_number = ""
            quantity_str = "" # Chuỗi hiển thị: "100 Viên / 50 Vỉ"
            percentage = 0
            is_filled = False

            if hasattr(tray, 'location') and tray.location:
                loc = tray.location
                if loc.product:
                    is_filled = True
                    product_obj = loc.product
                    if loc.batch:
                        batch_number = loc.batch.batch_number
                    
                    # Lấy tên đơn vị
                    qty_uom_name = loc.quantity_uom.name if loc.quantity_uom else ""
                    cap_uom_name = loc.capacity_uom.name if loc.capacity_uom else ""
                    
                    # Tạo chuỗi hiển thị
                    quantity_str = f"{loc.quantity} {qty_uom_name} / {loc.capacity} {cap_uom_name}"

                    # TÍNH PHẦN TRĂM CHÍNH XÁC (DÙNG LOGIC BOM)
                    if loc.capacity > 0:
                        # Quy đổi Quantity về đơn vị của Capacity
                        factor = get_conversion_factor(
                            loc.product_id, 
                            loc.quantity_uom_id, 
                            loc.capacity_uom_id, 
                            all_boms_list
                        )
                        converted_qty = loc.quantity * factor
                        percentage = (converted_qty / loc.capacity) * 100
                        
                        # Làm tròn
                        percentage = round(percentage, 1)
                        if percentage > 100: percentage = 100

            trays_info.append({
                'level': tray.level,
                'product': product_obj,
                'batch_number': batch_number,
                'quantity_str': quantity_str, # Dùng chuỗi này để hiện ở template
                'percentage': percentage,
                'is_filled': is_filled
            })
        shelf_data.append({'name': shelf.name, 'trays': trays_info})

    context = {
        'carousel': carousel,
        'shelf_data': shelf_data,
        'all_shelf_names': [s.name for s in shelves]
    }
    return render(request, 'carousel/control_panel.html', context)


# =======================================================
#               API: TRẢ VỀ TRẠNG THÁI KỆ
# =======================================================
@login_required
@admin_required
def api_get_status(request):
    carousel = Carousel.objects.first()
    if not carousel: return JsonResponse({'error': 'Carousel not initialized'}, status=404)
    return JsonResponse({
        'current_shelf': carousel.current_shelf_at_gate,
        'target_shelf': carousel.target_shelf,
        'is_moving': carousel.is_moving,
    })

# =======================================================
#               API: LỆNH HOMING
# =======================================================
@login_required
@admin_required
@require_POST
def api_homing(request):
    return _handle_move_request('A', is_homing=True)

# =======================================================
#               API: DI CHUYỂN ĐẾN KỆ CỤ THỂ
# =======================================================
@login_required
@admin_required
@require_POST
def api_move_to_shelf(request):
    target_shelf = request.POST.get('shelf_name', '').upper()
    return _handle_move_request(target_shelf)


# =======================================================
#               HÀM LOGIC DI CHUYỂN KỆ
# =======================================================
def _handle_move_request(target_shelf, is_homing=False):
    command_type = "HOMING" if is_homing else "MOVE"
    valid_shelves = list(Shelf.objects.values_list('name', flat=True))
    if not target_shelf or target_shelf not in valid_shelves:
        return JsonResponse({'status': 'error', 'message': 'Tên kệ không hợp lệ.'}, status=400)

    try:
        with transaction.atomic():
            carousel = Carousel.objects.select_for_update().first()
            if carousel.is_moving:
                return JsonResponse({'status': 'error', 'message': 'Kệ đang di chuyển, vui lòng chờ.'}, status=409)
            if carousel.current_shelf_at_gate == target_shelf:
                return JsonResponse({'status': 'ok', 'message': 'Kệ đã ở đúng vị trí.', 'path': []})
            
            path = _calculate_path(carousel.current_shelf_at_gate, target_shelf, valid_shelves)
            
            # Cập nhật trạng thái "đích" và cờ "is_moving"
            start_shelf = carousel.current_shelf_at_gate
            carousel.target_shelf = target_shelf
            carousel.is_moving = True
            carousel.save()

            duration = len(path) * 3 
            thread = threading.Thread(target=simulate_hardware_move, args=(start_shelf, path, duration))
            thread.start()

            logger.info(f"[HARDWARE SIGNAL] Received {command_type} command. Target: {target_shelf}")
            return JsonResponse({
                'status': 'ok',
                'message': f'Đã gửi lệnh di chuyển đến kệ {target_shelf}.',
                'path': path,
                'start_shelf': start_shelf,
                'target_shelf': target_shelf,
                'duration_per_step': 3000
            })
    except Exception as e:
        logger.error(f"Lỗi khi xử lý lệnh di chuyển: {e}")
        return JsonResponse({'status': 'error', 'message': 'Lỗi hệ thống.'}, status=500)

# =======================================================
#               HÀM TÍNH LỘ TRÌNH
# =======================================================
def _calculate_path(current_shelf, target_shelf, shelf_names):
    """
    Tính toán lộ trình di chuyển ngắn nhất.
    """
    n = len(shelf_names)
    current_index = shelf_names.index(current_shelf)
    target_index = shelf_names.index(target_shelf)
    
    # Tính toán đường đi xuôi
    path_forward = []
    i = current_index
    while i != target_index:
        i = (i + 1) % n
        path_forward.append(shelf_names[i])
        
    # Tính toán đường đi ngược
    path_backward = []
    i = current_index
    while i != target_index:
        i = (i - 1 + n) % n
        path_backward.append(shelf_names[i])

    # Chọn đường đi ngắn nhất
    return path_forward if len(path_forward) <= len(path_backward) else path_backward

# =======================================================
#               HÀM MÔ PHỎNG PHẦN CỨNG
# =======================================================
def simulate_hardware_move(start_shelf, path, total_duration):
    logger.info(f"--- [SIMULATION START] Moving from {start_shelf} to {path[-1]}. Will take {total_duration}s. ---")
    time.sleep(total_duration)
    
    with transaction.atomic():
        carousel = Carousel.objects.select_for_update().first()
        carousel.current_shelf_at_gate = carousel.target_shelf
        carousel.is_moving = False
        carousel.target_shelf = None
        carousel.save()

    logger.info(f"--- [SIMULATION END] Move complete. Carousel is now at {carousel.current_shelf_at_gate}. ---")

