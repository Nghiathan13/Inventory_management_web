import logging
import json
import redis
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.conf import settings

# Models
from products.models import Product, BillOfMaterials, UnitOfMeasure
from .models import Carousel, Shelf, StockLocation
from main.decorators import admin_required

logger = logging.getLogger(__name__)

# Cấu hình Redis
REDIS_HOST = 'localhost'
REDIS_PORT = 6379

def get_redis_client():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

# =======================================================
#        HELPER: THUẬT TOÁN QUY ĐỔI BOM (BFS)
# =======================================================
def get_conversion_factor(product_id, from_uom_id, to_uom_id, all_boms_list):
    """
    Tính hệ số quy đổi giữa 2 đơn vị bất kỳ (Hộp -> Vỉ -> Viên).
    """
    if not from_uom_id or not to_uom_id: return 1
    if from_uom_id == to_uom_id: return 1

    # 1. Xây dựng đồ thị
    graph = {}
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
    
    return 1 # Mặc định

# =======================================================
#        VIEW CHÍNH: CONTROL PANEL
# =======================================================
@login_required
@admin_required
def control_panel(request):
    carousel = Carousel.objects.first()
    if not carousel:
        return render(request, 'carousel/initial_setup_required.html')
        
    # Lấy danh sách kệ, sắp xếp theo tên (Giả sử tên là "1", "2"...)
    # Lưu ý: Cần đảm bảo tên kệ trong DB là số hoặc sắp xếp đúng logic mong muốn
    shelves = Shelf.objects.prefetch_related(
        'trays__location__product',
        'trays__location__batch',
        'trays__location__quantity_uom',
        'trays__location__capacity_uom'
    ).order_by('name')

    # 1. Lấy dữ liệu BOM để tính %
    all_boms_list = list(BillOfMaterials.objects.values('product_id', 'uom_from_id', 'uom_to_id', 'conversion_factor'))
    
    # Chuẩn bị dữ liệu Safe JSON cho JS
    safe_boms_data = []
    for bom in all_boms_list:
        safe_boms_data.append({
            'product_id': bom['product_id'],
            'uom_from_id': bom['uom_from_id'],
            'uom_to_id': bom['uom_to_id'],
            'conversion_factor': float(bom['conversion_factor'])
        })

    # 2. Dữ liệu Products (cho Modal)
    all_products_data = list(Product.objects.values(
        'id', 'code', 'name', 'uom_category_id', 'base_uom_id', 'base_uom__name'
    ))

    # 3. Dữ liệu UoM (cho Modal)
    all_uoms = UnitOfMeasure.objects.values('id', 'name', 'category_id')
    uoms_by_category_data = {}
    for uom in all_uoms:
        cat_id = uom['category_id']
        if cat_id not in uoms_by_category_data: uoms_by_category_data[cat_id] = []
        uoms_by_category_data[cat_id].append({'id': uom['id'], 'name': uom['name']})

    # 4. Xử lý dữ liệu hiển thị Kệ
    shelf_data = []
    all_shelf_names = []
    all_locations_data = [] # Data JSON cho JS

    for shelf in shelves:
        all_shelf_names.append(shelf.name)
        trays_info = []
        for tray in shelf.trays.all():
            # Item hiển thị HTML
            item = {
                'id': tray.id,
                'level': tray.level,
                'product': None,
                'batch_number': "",
                'quantity_str': "",
                'percentage': 0,
                'is_filled': False
            }

            if hasattr(tray, 'location') and tray.location:
                loc = tray.location
                
                # Thêm vào list JSON data cho Modal JS
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

                # Logic hiển thị UI
                if loc.product:
                    item['is_filled'] = True
                    item['product'] = loc.product
                    item['batch_number'] = loc.batch.batch_number if loc.batch else ""
                    
                    qty_name = loc.quantity_uom.name if loc.quantity_uom else ""
                    cap_name = loc.capacity_uom.name if loc.capacity_uom else ""
                    item['quantity_str'] = f"{loc.quantity} {qty_name} / {loc.capacity} {cap_name}"

                    if loc.capacity > 0:
                        factor = get_conversion_factor(loc.product_id, loc.quantity_uom_id, loc.capacity_uom_id, all_boms_list)
                        converted_qty = loc.quantity * factor
                        pct = (converted_qty / loc.capacity) * 100
                        item['percentage'] = round(pct, 1)
                        if item['percentage'] > 100: item['percentage'] = 100

            trays_info.append(item)
        shelf_data.append({'name': shelf.name, 'trays': trays_info})

    context = {
        'carousel': carousel,
        'shelf_data': shelf_data,
        'all_shelf_names': all_shelf_names,
        # Truyền dữ liệu JSON xuống Client
        'all_products_data': all_products_data,
        'uoms_by_category_data': uoms_by_category_data,
        'all_boms_data': safe_boms_data,
        'all_locations_data': all_locations_data, # Dùng key này khớp với json_script
    }
    return render(request, 'carousel/control_panel.html', context)


# =======================================================
#        API: LẤY TRẠNG THÁI (POLLING TỪ REDIS)
# =======================================================
@login_required
def api_get_status(request):
    try:
        r = get_redis_client()
        
        # 1. Kệ hiện tại (Logic Số 1-8)
        raw_shelf = r.get('current_shelf')
        current_shelf = 1 # Mặc định Kệ 1
        
        if raw_shelf:
            try:
                # Cố gắng parse sang số nguyên để JS dễ xử lý
                current_shelf = int(raw_shelf)
            except ValueError:
                current_shelf = 1

        # 2. Trạng thái Moving
        sys_status = r.get('system_status')
        is_moving = (sys_status == 'moving')

        # 3. Dropoff Data
        # Worker lưu dạng "shelf:tray" (ví dụ: "3:2")
        dropoff_content = r.get('dropoff_content:1')
        dropoff_data = None
        
        if dropoff_content and ":" in dropoff_content:
            try:
                s_str, t_str = dropoff_content.split(':')
                dropoff_data = {
                    'shelf': int(s_str), 
                    'tray': int(t_str)
                }
            except: 
                pass

        # 4. Lấy danh sách khay đang ở ngoài (OUT)
        # Worker lưu key dạng "tray_status:shelf:tray" giá trị là "out"
        grid_out = []
        for s in range(1, 9): # Kệ 1 đến 8
            for t in range(1, 3): # Tầng 1 đến 2
                status = r.get(f"tray_status:{s}:{t}")
                if status == "out":
                    grid_out.append({'shelf': s, 'tray': t})

        return JsonResponse({
            'current_shelf': current_shelf, # Int
            'is_moving': is_moving,
            'dropoff_data': dropoff_data, # {shelf: 1, tray: 2} hoặc None
            'grid_out': grid_out          # [{shelf: 3, tray: 1}, ...]
        })

    except Exception as e:
        return JsonResponse({'current_shelf': 1, 'is_moving': False, 'error': str(e)})

# =======================================================
#        API: GỬI LỆNH ĐIỀU KHIỂN
# =======================================================

@login_required
@admin_required
@require_POST
def api_homing(request):
    # Đẩy lệnh HOMING vào Redis Queue
    try:
        r = get_redis_client()
        task = {"cmd": "HOMING"}
        r.rpush('queue:high', json.dumps(task))
        return JsonResponse({'status': 'ok', 'message': 'Đã gửi lệnh HOMING'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
@admin_required
@require_POST
def api_move_to_shelf(request):
    """
    API này dùng để di chuyển kệ đến vị trí chỉ định (chỉ xoay, không gắp).
    Thường dùng cho nút điều khiển nhanh hoặc debug.
    """
    target_shelf_val = request.POST.get('shelf_name', '').strip()
    
    try:
        # Validate số kệ 1-8
        target_idx = int(target_shelf_val)
        if not (1 <= target_idx <= 8):
            return JsonResponse({'status': 'error', 'message': 'Kệ phải từ 1 đến 8'}, 400)
        
        r = get_redis_client()
        
        # Gửi lệnh FETCH ảo (Tray 1) để Worker thực hiện xoay kệ
        # Worker sẽ nhận lệnh, xoay kệ đến target, rồi gantry hoạt động.
        # Nếu muốn chỉ xoay mà không gantry, Worker cần hỗ trợ lệnh riêng (vd: MOVE)
        # Ở đây ta giả định dùng FETCH để kệ xoay tới đó.
        task = {
            "cmd": "FETCH", 
            "shelf": target_idx,
            "tray": 1 # Mặc định tầng 1
        }
        r.rpush('queue:medium', json.dumps(task))
        
        # Cập nhật trạng thái moving ngay để UI phản hồi
        r.set('system_status', 'moving')

        return JsonResponse({'status': 'ok', 'message': f'Đang di chuyển đến Kệ {target_idx}'})
    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'Tên kệ không hợp lệ (phải là số)'}, 400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})