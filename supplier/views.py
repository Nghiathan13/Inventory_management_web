# =======================================================
#               KHAI BÁO THƯ VIỆN (IMPORTS)
# =======================================================
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.http import HttpResponse, JsonResponse

# Decorators
from main.decorators import supplier_required
from inventory.models import PurchaseOrder, PurchaseOrderDetail

# Utilities cho việc tạo PDF và mã QR
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
import qrcode

# =======================================================
#               VIEWS CHO SUPPLIER PORTAL
# =======================================================

# -------------------------------------------------------
#   VIEW: TRANG CHỦ (DASHBOARD) CỦA SUPPLIER
# -------------------------------------------------------
@login_required
@supplier_required
def supplier_dashboard(request):
    pending_orders = PurchaseOrder.objects.filter(
        supplier=request.user,
        status='To Confirm'
    ).order_by('-created_at')
    
    history_orders = PurchaseOrder.objects.filter(
        supplier=request.user
    ).exclude(status='To Confirm').order_by('-confirmed_at', '-created_at')
    
    context = {
        'pending_orders': pending_orders,
        'history_orders': history_orders,
    }
    return render(request, 'supplier/dashboard.html', context)

# -------------------------------------------------------
#   VIEW: TRANG XỬ LÝ CHI TIẾT ĐƠN HÀNG
# -------------------------------------------------------
@login_required
@supplier_required
def process_order(request, pk):
    order = get_object_or_404(PurchaseOrder.objects.prefetch_related('details__product'), pk=pk, supplier=request.user)
    
    if order.status != 'To Confirm':
        messages.warning(request, f"Đơn hàng #{order.id} đã được xử lý trước đó.")
        return redirect('supplier:dashboard')

    context = {'order': order}
    return render(request, 'supplier/process_order.html', context)

# -------------------------------------------------------
#   VIEW: XÁC NHẬN ĐƠN HÀNG (CONFIRM ORDER)
# -------------------------------------------------------
@login_required
@supplier_required
def confirm_order_api(request, pk):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

    order = get_object_or_404(PurchaseOrder, pk=pk, supplier=request.user)
    
    if order.status != 'To Confirm':
        return JsonResponse({'status': 'warning', 'message': f'Order #{order.id} has already been processed.'})

    confirmed_detail_ids = request.POST.getlist('details')

    if not confirmed_detail_ids:
        return JsonResponse({'status': 'error', 'message': 'Bạn chưa chọn sản phẩm nào.'}, status=400)
    
    try:
        with transaction.atomic():
            # 1. Lưu hạn sử dụng cho các sản phẩm được chọn
            for detail_id in confirmed_detail_ids:
                expiry_date_str = request.POST.get(f'expiry_date_{detail_id}')
                
                # Kiểm tra bắt buộc nhập HSD
                if not expiry_date_str:
                    return JsonResponse({'status': 'error', 'message': f'Vui lòng nhập Hạn sử dụng cho tất cả sản phẩm được chọn.'}, status=400)
                
                detail = PurchaseOrderDetail.objects.get(id=detail_id)
                detail.expiry_date = expiry_date_str
                detail.save()

            # 2. Xóa các sản phẩm KHÔNG được chọn (Supplier không cung cấp)
            order.details.exclude(id__in=confirmed_detail_ids).delete()

            # 3. Cập nhật trạng thái đơn hàng
            order.status = 'Confirmed'
            order.confirmed_at = timezone.now()
            order.save()
            
            download_url = reverse('supplier:download_delivery_note', args=[order.pk])
            
            return JsonResponse({
                'status': 'success',
                'message': f'Đã xác nhận đơn hàng #{order.id} thành công.',
                'download_url': download_url
            })
            
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# -------------------------------------------------------
#   VIEW: LỊCH SỬ ĐƠN HÀNG CỦA SUPPLIER
# -------------------------------------------------------
@login_required
@supplier_required
def order_history(request):
    confirmed_orders = PurchaseOrder.objects.filter(
        supplier=request.user
    ).exclude(status='To Confirm').order_by('-confirmed_at', '-created_at')
    
    context = {'confirmed_orders': confirmed_orders}
    return render(request, 'supplier/order_history.html', context)

# -------------------------------------------------------
#   VIEW: TẢI PHIẾU GIAO HÀNG (DOWNLOAD DELIVERY NOTE)
# -------------------------------------------------------
@login_required
@supplier_required
def download_delivery_note_pdf(request, pk):
    po = get_object_or_404(PurchaseOrder.objects.prefetch_related('details__product__base_uom'), pk=pk, supplier=request.user)
    pdf_buffer = BytesIO()
    p = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter

    # 1. Vẽ Tiêu Đề Chính
    p.setFont("Helvetica-Bold", 22)
    p.drawCentredString(width / 2.0, height - 1 * inch, "Delivery Note")
    p.setFont("Helvetica", 14)
    p.drawCentredString(width / 2.0, height - 1.3 * inch, f"(For Order #{po.id})")

    # a. Tạo URL cho trang tiếp nhận đơn hàng, sử dụng unique_code của PurchaseOrder
    receive_po_url = request.build_absolute_uri(
        reverse('inventory:receive_po', args=[po.unique_code])
    )
    
    # b. Tạo ảnh mã QR từ URL trên
    qr_po_img = qrcode.make(receive_po_url)
    qr_po_buffer = BytesIO()
    qr_po_img.save(qr_po_buffer, format='PNG')
    qr_po_buffer.seek(0)
    
    # c. Vẽ mã QR tổng lên góc trên bên phải của trang
    p.drawImage(ImageReader(qr_po_buffer), 
                width - 2.0 * inch, height - 2.5 * inch, 
                width=1.5*inch, height=1.5*inch)

    # 2. Vẽ Thông Tin Phụ
    p.setFont("Helvetica", 11)
    p.drawString(1 * inch, height - 2 * inch, f"Supplier: {po.supplier.username}")
    p.drawString(1 * inch, height - 2.2 * inch, f"Confirmation Date: {po.confirmed_at.strftime('%d/%m/%Y %H:%M') if po.confirmed_at else 'N/A'}")

    p.line(1 * inch, height - 2.5 * inch, width - 1 * inch, height - 2.5 * inch)
    
    y_position = height - 3 * inch
    
    # 3. Vòng lặp vẽ thông tin và mã QR cho từng sản phẩm (giữ nguyên)
    y_position = height - 3 * inch
    
    for detail in po.details.all():
        if y_position < 2 * inch:
            p.showPage()
            y_position = height - 1 * inch
            p.setFont("Helvetica-Bold", 12)
            p.drawString(1 * inch, y_position, f"(Continued) - Delivery Note PO #{po.id}")
            y_position -= 0.5 * inch

        # Vẽ thông tin sản phẩm
        p.setFont("Helvetica-Bold", 12)
        p.drawString(1 * inch, y_position, f"- {detail.product.name}")
        
        p.setFont("Helvetica", 10)
        # Dòng 1: Số lượng
        p.drawString(1.2 * inch, y_position - 0.2 * inch, f"Qty: {detail.quantity} {detail.product.base_uom.name if detail.product.base_uom else ''}")
        # Dòng 2: Mã sản phẩm
        p.drawString(1.2 * inch, y_position - 0.35 * inch, f"Code: {detail.product.code}")
        # Dòng 3: Hạn sử dụng (MỚI THÊM)
        expiry_str = detail.expiry_date.strftime('%d/%m/%Y') if detail.expiry_date else "N/A"
        p.drawString(1.2 * inch, y_position - 0.5 * inch, f"Exp Date: {expiry_str}")
        
        # Vẽ QR Code cho từng sản phẩm
        stock_in_api_url = request.build_absolute_uri(
            reverse('inventory:stock_in_process_api', args=[detail.unique_code])
        )
        qr_item_img = qrcode.make(stock_in_api_url)
        qr_item_buffer = BytesIO()
        qr_item_img.save(qr_item_buffer, format='PNG')
        qr_item_buffer.seek(0)
        
        p.drawImage(ImageReader(qr_item_buffer), 
                    width - 2.0 * inch, y_position - 0.8 * inch, 
                    width=1*inch, height=1*inch)
        
        y_position -= 1.5 * inch # Tăng khoảng cách để chứa thêm dòng HSD

    p.showPage()
    p.save()
    pdf_buffer.seek(0)
    
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="phieu_giao_hang_{po.id}.pdf"'
    return response