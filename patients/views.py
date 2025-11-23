from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

# Models
from .models import Patient
from doctor.models import Prescription

# Forms 
from .forms import PatientForm

# Decorators
from main.decorators import admin_or_doctor_required

# =======================================================
#               QUẢN LÝ BỆNH NHÂN (PATIENT CRUD)
# =======================================================

# -------------------------------------------------------
#   VIEW: DANH SÁCH BỆNH NHÂN (READ)
# -------------------------------------------------------
@login_required
@admin_or_doctor_required
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
    return render(request, 'patients/list.html', context)

# -------------------------------------------------------
#   VIEW: THÊM BỆNH NHÂN (CREATE)
# -------------------------------------------------------
@login_required
@admin_or_doctor_required
def patient_add(request):
    if request.method == 'POST':
        form = PatientForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã thêm hồ sơ bệnh nhân mới thành công.')
            return redirect('patients:list')
    else:
        form = PatientForm()

    context = {
        'form': form, 
        'title': 'Thêm Hồ Sơ Bệnh Nhân'
    }
    return render(request, 'patients/form.html', context)

# -------------------------------------------------------
#   VIEW: CẬP NHẬT BỆNH NHÂN (UPDATE)
# -------------------------------------------------------
@login_required
@admin_or_doctor_required
def patient_update(request, pk):
    patient = Patient.objects.get(id=pk)
    if request.method == 'POST':
        form = PatientForm(request.POST, request.FILES, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, f'Đã cập nhật hồ sơ cho bệnh nhân {patient.full_name}.')
            return redirect('patients:list')
    else:
        form = PatientForm(instance=patient)

    context = {
        'form': form, 
        'title': 'Cập Nhật Hồ Sơ Bệnh Nhân'
    }
    return render(request, 'patients/form.html', context)

# -------------------------------------------------------
#   VIEW: XÓA BỆNH NHÂN (DELETE)
# -------------------------------------------------------
@login_required
@admin_or_doctor_required
def patient_delete(request, pk):
    patient = Patient.objects.get(id=pk)
    if request.method == 'POST':
        patient.delete()
        messages.success(request, f'Đã xóa hồ sơ của bệnh nhân {patient.full_name}.')
        return redirect('patients:list')
    
    context = {
        'item': patient
    }
    return render(request, 'patients/confirm_delete.html', context)

# -------------------------------------------------------
#   VIEW: CHI TIẾT HỒ SƠ BỆNH NHÂN (READ DETAIL)
# -------------------------------------------------------
@login_required
@admin_or_doctor_required
def patient_detail(request, pk):
    try:
        patient = Patient.objects.get(id=pk)
        prescriptions = Prescription.objects.filter(patient=patient).order_by('-created_at')
        context = {
            'patient': patient,
            'prescriptions': prescriptions,
        }
        return render(request, 'patients/detail.html', context)
    except Patient.DoesNotExist:
        messages.error(request, 'Hồ sơ bệnh nhân không tồn tại.')
        return redirect('patients:list')
    