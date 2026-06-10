from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect
from hospital.views import is_patient
from .facades import PatientFacade  # Підключаємо наш новий фасад
from . import forms


def patient_signup_view(request):
    userForm = forms.PatientUserForm()
    patientForm = forms.PatientForm()
    mydict = {'userForm': userForm, 'patientForm': patientForm}

    if request.method == 'POST':
        userForm = forms.PatientUserForm(request.POST)
        patientForm = forms.PatientForm(request.POST, request.FILES)
        if userForm.is_valid() and patientForm.is_valid():
            PatientFacade.register_new_patient(
                user_form=userForm,
                patient_form=patientForm,
                assigned_doctor_id=request.POST.get('assignedDoctorId')
            )
            return HttpResponseRedirect('patientlogin')

    return render(request, 'patient/patientsignup.html', context=mydict)


@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_dashboard_view(request):
    # Отримуємо зведений аналітичний контекст через одну команду фасаду
    mydict = PatientFacade.get_dashboard_context(request.user.id)
    return render(request, 'patient/patient_dashboard.html', context=mydict)


@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_appointment_view(request):
    patient_profile = PatientFacade.get_patient_profile(request.user.id)
    return render(request, 'patient/patient_appointment.html', {'patient': patient_profile})


@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_book_appointment_view(request):
    appointmentForm = forms.PatientAppointmentForm()
    patient_profile = PatientFacade.get_patient_profile(request.user.id)

    if request.method == 'POST':
        appointmentForm = forms.PatientAppointmentForm(request.POST)
        if appointmentForm.is_valid():
            PatientFacade.book_appointment(
                user=request.user,
                appointment_form=appointmentForm,
                doctor_id=request.POST.get('doctorId')
            )
            return HttpResponseRedirect('patient-view-appointment')

    return render(request, 'patient/patient_book_appointment.html', {
        'appointmentForm': appointmentForm,
        'patient': patient_profile,
        'message': None
    })


def patient_view_doctor_view(request):
    doctors_list = PatientFacade.get_active_doctors()
    patient_profile = PatientFacade.get_patient_profile(request.user.id)
    return render(request, 'patient/patient_view_doctor.html', {'doctors': doctors_list, 'patient': patient_profile})


def search_doctor_view(request):
    query = request.GET['query']
    doctors_list = PatientFacade.search_doctors(query)
    patient_profile = PatientFacade.get_patient_profile(request.user.id)
    return render(request, 'patient/patient_view_doctor.html', {'doctors': doctors_list, 'patient': patient_profile})


@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_view_appointment_view(request):
    appointments_list = PatientFacade.get_patient_appointments(request.user.id)
    patient_profile = PatientFacade.get_patient_profile(request.user.id)
    return render(request, 'patient/patient_view_appointment.html',
                  {'appointments': appointments_list, 'patient': patient_profile})


@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_discharge_view(request):
    patient_dict = PatientFacade.get_discharge_details_context(request.user.id)
    return render(request, 'patient/patient_discharge.html', context=patient_dict)