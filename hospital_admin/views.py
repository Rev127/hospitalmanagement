from django.shortcuts import render, redirect, reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect, HttpResponse
from hospital.views import is_admin
from .facades import AdminFacade  # Імпортуємо наш новий фасад адміністратора
from . import forms
import io
from xhtml2pdf import pisa
from django.template.loader import get_template


def admin_signup_view(request):
    form = forms.AdminSigupForm()
    if request.method == 'POST':
        form = forms.AdminSigupForm(request.POST)
        if form.is_valid():
            AdminFacade.register_admin(form)
            return HttpResponseRedirect('adminlogin')
    return render(request, 'hospital/adminsignup.html', {'form': form})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_dashboard_view(request):
    context = AdminFacade.get_dashboard_context()
    return render(request, 'hospital/admin_dashboard.html', context=context)


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_doctor_view(request):
    return render(request, 'hospital/admin_doctor.html')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_doctor_view(request):
    doctors = AdminFacade.get_approved_doctors()
    return render(request, 'hospital/admin_view_doctor.html', {'doctors': doctors})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def delete_doctor_from_hospital_view(request, pk):
    AdminFacade.delete_doctor(pk)
    return redirect('admin-view-doctor')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def update_doctor_view(request, pk):
    from doctor.models import Doctor
    doctor = Doctor.objects.get(id=pk)
    user = User.objects.get(id=doctor.user_id)
    from doctor.forms import DoctorUserForm, DoctorForm

    userForm = DoctorUserForm(instance=user)
    doctorForm = DoctorForm(request.FILES, instance=doctor)

    if request.method == 'POST':
        userForm = DoctorUserForm(request.POST, instance=user)
        doctorForm = DoctorForm(request.POST, request.FILES, instance=doctor)
        if userForm.is_valid() and doctorForm.is_valid():
            AdminFacade.save_doctor(userForm, doctorForm, user_instance=user, doctor_instance=doctor)
            return redirect('admin-view-doctor')
    return render(request, 'hospital/admin_update_doctor.html',
                  context={'userForm': userForm, 'doctorForm': doctorForm})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_doctor_view(request):
    from doctor.forms import DoctorUserForm, DoctorForm
    userForm = DoctorUserForm()
    doctorForm = DoctorForm()

    if request.method == 'POST':
        userForm = DoctorUserForm(request.POST)
        doctorForm = DoctorForm(request.POST, request.FILES)
        if userForm.is_valid() and doctorForm.is_valid():
            AdminFacade.save_doctor(userForm, doctorForm)
            return HttpResponseRedirect('admin-view-doctor')
    return render(request, 'hospital/admin_add_doctor.html', context={'userForm': userForm, 'doctorForm': doctorForm})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_approve_doctor_view(request):
    doctors = AdminFacade.get_pending_doctors()
    return render(request, 'hospital/admin_approve_doctor.html', {'doctors': doctors})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_doctor_view(request, pk):
    AdminFacade.approve_doctor(pk)
    return redirect(reverse('admin-approve-doctor'))


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def reject_doctor_view(request, pk):
    AdminFacade.delete_doctor(pk)
    return redirect('admin-approve-doctor')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_doctor_specialisation_view(request):
    doctors = AdminFacade.get_approved_doctors()
    return render(request, 'hospital/admin_view_doctor_specialisation.html', {'doctors': doctors})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_patient_view(request):
    return render(request, 'hospital/admin_patient.html')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_patient_view(request):
    patients = AdminFacade.get_approved_patients()
    return render(request, 'hospital/admin_view_patient.html', {'patients': patients})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def delete_patient_from_hospital_view(request, pk):
    AdminFacade.delete_patient(pk)
    return redirect('admin-view-patient')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def update_patient_view(request, pk):
    from patient.models import Patient
    patient = Patient.objects.get(id=pk)
    user = User.objects.get(id=patient.user_id)
    from patient.forms import PatientUserForm, PatientForm

    userForm = PatientUserForm(instance=user)
    patientForm = PatientForm(request.FILES, instance=patient)

    if request.method == 'POST':
        userForm = PatientUserForm(request.POST, instance=user)
        patientForm = PatientForm(request.POST, request.FILES, instance=patient)
        if userForm.is_valid() and patientForm.is_valid():
            AdminFacade.save_patient(userForm, patientForm, request.POST.get('assignedDoctorId'), user_instance=user,
                                     patient_instance=patient)
            return redirect('admin-view-patient')
    return render(request, 'hospital/admin_update_patient.html',
                  context={'userForm': userForm, 'patientForm': patientForm})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_patient_view(request):
    from patient.forms import PatientUserForm, PatientForm
    userForm = PatientUserForm()
    patientForm = PatientForm()

    if request.method == 'POST':
        userForm = PatientUserForm(request.POST)
        patientForm = PatientForm(request.POST, request.FILES)
        if userForm.is_valid() and patientForm.is_valid():
            AdminFacade.save_patient(userForm, patientForm, request.POST.get('assignedDoctorId'))
            return HttpResponseRedirect('admin-view-patient')
    return render(request, 'hospital/admin_add_patient.html',
                  context={'userForm': userForm, 'patientForm': patientForm})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_approve_patient_view(request):
    patients = AdminFacade.get_pending_patients()
    return render(request, 'hospital/admin_approve_patient.html', {'patients': patients})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_patient_view(request, pk):
    AdminFacade.approve_patient(pk)
    return redirect(reverse('admin-approve-patient'))


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def reject_patient_view(request, pk):
    AdminFacade.delete_patient(pk)
    return redirect('admin-approve-patient')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_discharge_patient_view(request):
    patients = AdminFacade.get_approved_patients()
    return render(request, 'hospital/admin_discharge_patient.html', {'patients': patients})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def discharge_patient_view(request, pk):
    patient_dict = AdminFacade.get_discharge_initial_context(pk)
    if request.method == 'POST':
        updated_dict = AdminFacade.process_patient_discharge(pk, patient_dict, request.POST)
        return render(request, 'hospital/patient_final_bill.html', context=updated_dict)
    return render(request, 'hospital/patient_generate_bill.html', context=patient_dict)


def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None


def download_pdf_view(request, pk):
    bill = AdminFacade.get_latest_discharge_bill(pk)
    if not bill:
        return HttpResponse("Bill not found", status=404)
    return render_to_pdf('hospital/download_bill.html', {
        'patientName': bill.patientName, 'assignedDoctorName': bill.assignedDoctorName,
        'address': bill.address, 'mobile': bill.mobile, 'symptoms': bill.symptoms,
        'admitDate': bill.admitDate, 'releaseDate': bill.releaseDate, 'daySpent': bill.daySpent,
        'medicineCost': bill.medicineCost, 'roomCharge': bill.roomCharge, 'doctorFee': bill.doctorFee,
        'OtherCharge': bill.OtherCharge, 'total': bill.total,
    })


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_appointment_view(request):
    return render(request, 'hospital/admin_appointment.html')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_appointment_view(request):
    appointments = AdminFacade.get_approved_appointments()
    return render(request, 'hospital/admin_view_appointment.html', {'appointments': appointments})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_appointment_view(request):
    appointmentForm = forms.AppointmentForm()
    if request.method == 'POST':
        appointmentForm = forms.AppointmentForm(request.POST)
        if appointmentForm.is_valid():
            AdminFacade.create_appointment_by_admin(
                appointment_form=appointmentForm,
                doctor_id=request.POST.get('doctorId'),
                patient_id=request.POST.get('patientId')
            )
            return HttpResponseRedirect('admin-view-appointment')
    return render(request, 'hospital/admin_add_appointment.html', context={'appointmentForm': appointmentForm})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_approve_appointment_view(request):
    appointments = AdminFacade.get_pending_appointments()
    return render(request, 'hospital/admin_approve_appointment.html', {'appointments': appointments})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_appointment_view(request, pk):
    AdminFacade.approve_appointment(pk)
    return redirect(reverse('admin-approve-appointment'))


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def reject_appointment_view(request, pk):
    AdminFacade.delete_appointment(pk)
    return redirect('admin-approve-appointment')