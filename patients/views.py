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
#               QUẢN LÝ BỆNH NHÂN
# =======================================================

# -------------------------------------------------------
#   DANH SÁCH BỆNH NHÂN
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
#   THÊM BỆNH NHÂN
# -------------------------------------------------------
@login_required
@admin_or_doctor_required
def patient_add(request):
    if request.method == 'POST':
        form = PatientForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Patient record added successfully.')
            return redirect('patients:list')
    else:
        form = PatientForm()

    context = {
        'form': form, 
        'title': 'Add Patient Record'
    }
    return render(request, 'patients/form.html', context)

# -------------------------------------------------------
#   CẬP NHẬT BỆNH NHÂN
# -------------------------------------------------------
@login_required
@admin_or_doctor_required
def patient_update(request, pk):
    patient = get_object_or_404(Patient, id=pk)
    
    if request.method == 'POST':
        form = PatientForm(request.POST, request.FILES, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, f'Updated record for patient {patient.full_name}.')
            return redirect('patients:list')
    else:
        form = PatientForm(instance=patient)

    context = {
        'form': form, 
        'title': 'Update Patient Record'
    }
    return render(request, 'patients/form.html', context)

# -------------------------------------------------------
#   XÓA BỆNH NHÂN
# -------------------------------------------------------
@login_required
@admin_or_doctor_required
def patient_delete(request, pk):
    patient = get_object_or_404(Patient, id=pk)
    
    if request.method == 'POST':
        patient.delete()
        messages.success(request, f'Deleted record of patient {patient.full_name}.')
        return redirect('patients:list')
    
    context = {
        'item': patient
    }
    return render(request, 'patients/confirm_delete.html', context)

# -------------------------------------------------------
#   CHI TIẾT HỒ SƠ
# -------------------------------------------------------
@login_required
@admin_or_doctor_required
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, id=pk)
    prescriptions = Prescription.objects.filter(patient=patient).order_by('-created_at')
    
    context = {
        'patient': patient,
        'prescriptions': prescriptions,
    }
    return render(request, 'patients/detail.html', context)