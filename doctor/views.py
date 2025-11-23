from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.urls import reverse
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import F

# Models
from .models import Prescription, PrescriptionDetail
from products.models import Product, UnitOfMeasure, BillOfMaterials
from patients.models import Patient

# Forms
from .forms import PrescriptionForm

# Decorators
from main.decorators import admin_or_doctor_required, doctor_required

# Utilities cho PDF & QR
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from django.utils import timezone
import qrcode


# =======================================================
#        HELPER: THUẬT TOÁN QUY ĐỔI THÔNG MINH (BFS)
# =======================================================
def get_smart_conversion_factor(product_id, from_uom_id, to_uom_id, all_boms_list):
    """
    Tìm hệ số quy đổi giữa 2 đơn vị bất kỳ bằng thuật toán tìm đường (BFS).
    Hỗ trợ: Xuôi, Ngược, Bắc cầu (Ví dụ: Hộp -> Vỉ -> Viên).
    """
    if not from_uom_id or not to_uom_id: return 1
    if from_uom_id == to_uom_id: return 1

    # 1. Xây dựng đồ thị quy đổi
    graph = {}
    # Lọc các rule của sản phẩm này
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
            return curr['factor'] # Tìm thấy đường đi

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
#               QUẢN LÝ KÊ ĐƠN (PRESCRIPTION)
# =======================================================

# -------------------------------------------------------
#   VIEW: TRANG KÊ ĐƠN THUỐC
# -------------------------------------------------------
@login_required
@admin_or_doctor_required
def prescription(request):
    """
    Xử lý việc tạo và hiển thị lịch sử các toa thuốc.
    """
    if request.method == 'POST':
        prescription_form = PrescriptionForm(request.POST)
        if prescription_form.is_valid():
           
            # --- THU THẬP DỮ LIỆU FORM ĐỘNG ---
            details_to_process = []
            processed_products = set()
           
            indices = sorted(list(set([key.split('-')[1] for key in request.POST if key.startswith('details-') and '-product' in key])))

            for index in indices:
                product_id_str = request.POST.get(f'details-{index}-product')
                quantity_str = request.POST.get(f'details-{index}-quantity')
                uom_id_str = request.POST.get(f'details-{index}-uom')

                if product_id_str and quantity_str and int(quantity_str) > 0 and uom_id_str:
                    product_id = int(product_id_str)
                    if product_id in processed_products:
                        messages.error(request, f"Sản phẩm bị trùng lặp. Vui lòng kiểm tra lại.")
                        return redirect('doctor:prescription')
                    processed_products.add(product_id)
                   
                    try:
                        product = Product.objects.get(id=product_id)
                        quantity = int(quantity_str)
                        uom_selected = UnitOfMeasure.objects.get(id=int(uom_id_str))
                       
                        # --- LOGIC QUY ĐỔI MỚI (SMART BOM) ---
                        
                        # 1. Lấy danh sách BOM của sản phẩm này
                        all_boms_list = list(BillOfMaterials.objects.filter(product=product).values(
                            'product_id', 'uom_from_id', 'uom_to_id', 'conversion_factor'
                        ))

                        # 2. Tính hệ số quy đổi từ Đơn vị kê đơn -> Đơn vị gốc (Base UoM)
                        conversion_factor = get_smart_conversion_factor(
                            product.id, 
                            uom_selected.id, 
                            product.base_uom_id, 
                            all_boms_list
                        )
                        
                        # 3. Tính số lượng cần trừ kho (theo Base Unit)
                        quantity_to_deduct = quantity * conversion_factor

                        # 4. Kiểm tra tồn kho
                        # (Dùng sai số nhỏ epsilon cho phép so sánh số thực an toàn hơn)
                        if product.quantity < (quantity_to_deduct - 0.0001):
                            # Tính ngược lại để hiển thị thông báo dễ hiểu
                            current_stock_in_selected_uom = product.quantity / conversion_factor
                            messages.error(
                                request, 
                                f"Không đủ thuốc '{product.name}'. "
                                f"Cần: {quantity} {uom_selected.name}. "
                                f"Kho chỉ còn tương đương: {current_stock_in_selected_uom:.2f} {uom_selected.name} "
                                f"({product.quantity} {product.base_uom.name})."
                            )
                            return redirect('doctor:prescription')
                       
                        details_to_process.append({
                            'product': product, 
                            'quantity': quantity, 
                            'uom': uom_selected
                        })

                    except (Product.DoesNotExist, UnitOfMeasure.DoesNotExist):
                        messages.error(request, "Dữ liệu thuốc hoặc đơn vị không hợp lệ.")
                        return redirect('doctor:prescription')

            # Kiểm tra danh sách rỗng
            if not details_to_process:
                messages.error(request, 'Toa thuốc phải có ít nhất một loại thuốc hợp lệ.')
                return redirect('doctor:prescription')
           
            # --- LƯU VÀO DATABASE ---
            try:
                with transaction.atomic():
                    new_prescription = prescription_form.save(commit=False)
                    new_prescription.doctor = request.user
                    new_prescription.status = 'Pending'
                    new_prescription.save()
                   
                    for item in details_to_process:
                        PrescriptionDetail.objects.create(
                            prescription=new_prescription,
                            product=item['product'],
                            quantity=item['quantity'],
                            uom=item['uom']
                        )
                    messages.success(request, f'Đã gửi toa thuốc cho bệnh nhân {new_prescription.patient.full_name} thành công.')
                    return redirect('doctor:prescription')
            except Exception as e:
                messages.error(request, f'Đã có lỗi xảy ra trong quá trình lưu: {e}')
        else:
            messages.error(request, 'Vui lòng kiểm tra lại thông tin bệnh nhân.')

    # --- LOGIC GET (HIỂN THỊ TRANG) ---
    prescription_form = PrescriptionForm()
   
    if request.user.is_superuser:
        prescriptions = Prescription.objects.all().order_by('-created_at')
    else:
        prescriptions = Prescription.objects.filter(doctor=request.user).order_by('-created_at')

    products_data = list(
        Product.objects.filter(quantity__gt=0).values('id', 'name', 'quantity', 'uom_category_id')
    )
   
    uoms_data = list(UnitOfMeasure.objects.values('id', 'name', 'category_id'))

    context = {
        'prescription_form': prescription_form,
        'prescriptions': prescriptions,
        'products_data': products_data,
        'uoms_data': uoms_data,
    }
    return render(request, 'doctor/prescription.html', context)

# =======================================================
#               XUẤT TOA THUỐC PDF VỚI MÃ QR
# =======================================================
@login_required
@doctor_required
def download_prescription_pdf(request, pk):
    prescription = get_object_or_404(
        Prescription.objects.prefetch_related(
            'details__product__base_uom',
            'details__uom',
        ),
        pk=pk
    )

    dispense_url = request.build_absolute_uri(
        reverse('inventory:dispense_process', args=[prescription.pk])
    )
   
    qr_img = qrcode.make(dispense_url)
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)

    pdf_buffer = BytesIO()
    p = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter

    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width / 2.0, height - 1 * inch, "ELECTRONIC PRESCRIPTION")

    p.setFont("Helvetica", 11)
    p.drawString(1 * inch, height - 1.5 * inch, f"Patient: {prescription.patient.full_name}")
    p.drawString(5 * inch, height - 1.5 * inch, f"Doctor: {prescription.doctor.get_full_name() or prescription.doctor.username}")
   
    created_at_local = timezone.localtime(prescription.created_at)
    created_time_str = created_at_local.strftime("%H:%M - %d/%m/%Y")
    p.setFont("Helvetica-Oblique", 10)
    p.setFillColor(colors.darkgrey)
    p.drawString(1 * inch, height - 1.7 * inch, f"Date Created: {created_time_str}")
   
    p.setStrokeColor(colors.lightgrey)
    p.line(1 * inch, height - 1.9 * inch, width - 1 * inch, height - 1.9 * inch)

    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(1 * inch, height - 2.2 * inch, "Medications:")
   
    y_position = height - 2.5 * inch
    p.setFont("Helvetica", 11)
    for detail in prescription.details.all():
        unit_name = detail.uom.name if detail.uom else detail.product.base_uom.name
        p.drawString(1.2 * inch, y_position, f"- {detail.product.name} (Quantity: {detail.quantity} {unit_name})")
        y_position -= 0.3 * inch

    p.drawImage(ImageReader(qr_buffer),
                width - 2.0 * inch, 0.75 * inch,
                width=1.5*inch, height=1.5*inch)

    p.showPage()
    p.save()
    pdf_buffer.seek(0)

    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="prescription_{prescription.id}.pdf"'
    return response