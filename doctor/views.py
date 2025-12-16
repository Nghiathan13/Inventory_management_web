from io import BytesIO
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.db.models import F

from .models import Prescription, PrescriptionDetail
from products.models import Product, UnitOfMeasure, BillOfMaterials
from .forms import PrescriptionForm
from main.decorators import admin_or_doctor_required, doctor_required


# =======================================================
#        QUY ĐỔI ĐƠN VỊ (BFS)
# =======================================================
def get_smart_conversion_factor(product_id, from_uom_id, to_uom_id, all_boms_list):
    if not from_uom_id or not to_uom_id: return 1
    if from_uom_id == to_uom_id: return 1

    # Xây dựng đồ thị
    graph = {}
    relevant_boms = [b for b in all_boms_list if b['product_id'] == product_id]

    for bom in relevant_boms:
        if bom['uom_from_id'] not in graph: graph[bom['uom_from_id']] = []
        graph[bom['uom_from_id']].append({'to': bom['uom_to_id'], 'factor': float(bom['conversion_factor'])})
        
        if bom['uom_to_id'] not in graph: graph[bom['uom_to_id']] = []
        graph[bom['uom_to_id']].append({'to': bom['uom_from_id'], 'factor': 1.0 / float(bom['conversion_factor'])})

    # Tìm đường đi
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
#        XỬ LÝ KÊ ĐƠN
# =======================================================
@login_required
@admin_or_doctor_required
def prescription(request):
    # Xử lý Form gửi lên
    if request.method == 'POST':
        prescription_form = PrescriptionForm(request.POST)
        if prescription_form.is_valid():
            details_to_process = []
            processed_products = set()
           
            # Lọc dữ liệu Form
            indices = sorted(list(set([key.split('-')[1] for key in request.POST if key.startswith('details-') and '-product' in key])))

            for index in indices:
                product_id_str = request.POST.get(f'details-{index}-product')
                quantity_str = request.POST.get(f'details-{index}-quantity')
                uom_id_str = request.POST.get(f'details-{index}-uom')

                if product_id_str and quantity_str and int(quantity_str) > 0 and uom_id_str:
                    product_id = int(product_id_str)
                    
                    # Kiểm tra trùng lặp
                    if product_id in processed_products:
                        messages.error(request, "Duplicate product selected.")
                        return redirect('doctor:prescription')
                    processed_products.add(product_id)
                   
                    try:
                        product = Product.objects.get(id=product_id)
                        quantity = int(quantity_str)
                        uom_selected = UnitOfMeasure.objects.get(id=int(uom_id_str))
                       
                        # Lấy dữ liệu quy đổi
                        all_boms_list = list(BillOfMaterials.objects.filter(product=product).values(
                            'product_id', 'uom_from_id', 'uom_to_id', 'conversion_factor'
                        ))

                        # Tính toán quy đổi
                        conversion_factor = get_smart_conversion_factor(
                            product.id, 
                            uom_selected.id, 
                            product.base_uom_id, 
                            all_boms_list
                        )
                        quantity_to_deduct = quantity * conversion_factor

                        # Kiểm tra tồn kho
                        if product.quantity < (quantity_to_deduct - 0.0001):
                            current_stock = product.quantity / conversion_factor
                            messages.error(
                                request, 
                                f"Insufficient stock for '{product.name}'. "
                                f"Need: {quantity} {uom_selected.name}. "
                                f"Have: {current_stock:.2f} {uom_selected.name}."
                            )
                            return redirect('doctor:prescription')
                       
                        details_to_process.append({
                            'product': product, 
                            'quantity': quantity, 
                            'uom': uom_selected
                        })

                    except (Product.DoesNotExist, UnitOfMeasure.DoesNotExist):
                        messages.error(request, "Invalid data.")
                        return redirect('doctor:prescription')

            if not details_to_process:
                messages.error(request, 'Prescription is empty.')
                return redirect('doctor:prescription')
           
            # Lưu dữ liệu
            try:
                with transaction.atomic():
                    new_prescription = prescription_form.save(commit=False)
                    new_prescription.doctor = request.user
                    new_prescription.status = 'Pending'
                    new_prescription.save()
                   
                    PrescriptionDetail.objects.bulk_create([
                        PrescriptionDetail(
                            prescription=new_prescription,
                            product=item['product'],
                            quantity=item['quantity'],
                            uom=item['uom']
                        ) for item in details_to_process
                    ])
                    
                    messages.success(request, f'Prescription created for {new_prescription.patient.full_name}.')
                    return redirect('doctor:prescription')
            except Exception as e:
                messages.error(request, f'System error: {e}')
        else:
            messages.error(request, 'Check patient info.')

    # Hiển thị giao diện
    prescription_form = PrescriptionForm()
    
    if request.user.is_superuser:
        prescriptions = Prescription.objects.all().order_by('-created_at')
    else:
        prescriptions = Prescription.objects.filter(doctor=request.user).order_by('-created_at')

    products_data = list(Product.objects.filter(quantity__gt=0).values('id', 'name', 'quantity', 'uom_category_id'))
    uoms_data = list(UnitOfMeasure.objects.values('id', 'name', 'category_id'))

    context = {
        'prescription_form': prescription_form,
        'prescriptions': prescriptions,
        'products_data': products_data,
        'uoms_data': uoms_data,
    }
    return render(request, 'doctor/prescription.html', context)


# =======================================================
#        XUẤT PDF & QR
# =======================================================
@login_required
@doctor_required
def download_prescription_pdf(request, pk):
    prescription = get_object_or_404(
        Prescription.objects.prefetch_related('details__product__base_uom', 'details__uom'),
        pk=pk
    )

    # Tạo QR Code
    dispense_url = request.build_absolute_uri(reverse('inventory:dispense_process', args=[prescription.pk]))
    qr_img = qrcode.make(dispense_url)
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)

    # Khởi tạo PDF
    pdf_buffer = BytesIO()
    p = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter

    

    # Vẽ tiêu đề
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(4 * inch, height - 1 * inch, "ELECTRONIC PRESCRIPTION")

    # Thông tin chung
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

    # Danh sách thuốc
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(1 * inch, height - 2.2 * inch, "Medications:")
   
    y_position = height - 2.5 * inch
    p.setFont("Helvetica", 11)
    for detail in prescription.details.all():
        unit_name = detail.uom.name if detail.uom else detail.product.base_uom.name
        p.drawString(1.2 * inch, y_position, f"- {detail.product.name} (Quantity: {detail.quantity} {unit_name})")
        y_position -= 0.3 * inch

    # Chèn ảnh QR
    p.drawImage(
        ImageReader(qr_buffer), 
        width - 1.7 * inch, 
        height - 1.7 * inch, 
        width=1.5*inch,     
        height=1.5*inch
    )

    p.showPage()
    p.save()
    pdf_buffer.seek(0)

    
    
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="prescription_{prescription.id}.pdf"'
    return response