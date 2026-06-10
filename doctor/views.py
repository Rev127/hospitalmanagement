from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect
from hospital.views import is_doctor
from .facades import DoctorFacade  # Підключаємо розроблений фасад лікаря
from . import forms


def doctor_signup_view(request):
    userForm = forms.DoctorUserForm()
    doctorForm = forms.DoctorForm()
    mydict = {'userForm': userForm, 'doctorForm': doctorForm}

    if request.method == 'POST':
        userForm = forms.DoctorUserForm(request.POST)
        doctorForm = forms.DoctorForm(request.POST, request.FILES)
        if userForm.is_valid() and doctorForm.is_valid():
            DoctorFacade.register_new_doctor(userForm, doctorForm)
        return HttpResponseRedirect('doctorlogin')

    return render(request, 'doctor/doctorsignup.html', context=mydict)


@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_dashboard_view(request):
    # Отримуємо весь аналітичний зріз даних через одну команду фасаду
    mydict = DoctorFacade.get_dashboard_context(request.user)
    return render(request, 'doctor/doctor_dashboard.html', context=mydict)


@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_patient_view(request):
    doctor_profile = DoctorFacade.get_doctor_profile(request.user.id)
    return render(request, 'doctor/doctor_patient.html', {'doctor': doctor_profile})


@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_view_patient_view(request):
    patients = DoctorFacade.get_assigned_patients(request.user.id)
    doctor_profile = DoctorFacade.get_doctor_profile(request.user.id)
    return render(request, 'doctor/doctor_view_patient.html', {'patients': patients, 'doctor': doctor_profile})


@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def search_view(request):
    query = request.GET['query']
    patients = DoctorFacade.search_assigned_patients(request.user.id, query)
    doctor_profile = DoctorFacade.get_doctor_profile(request.user.id)
    return render(request, 'doctor/doctor_view_patient.html', {'patients': patients, 'doctor': doctor_profile})


@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_view_discharge_patient_view(request):
    discharged = DoctorFacade.get_discharged_patients(request.user.first_name)
    doctor_profile = DoctorFacade.get_doctor_profile(request.user.id)
    return render(request, 'doctor/doctor_view_discharge_patient.html',
                  {'dischargedpatients': discharged, 'doctor': doctor_profile})


@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_appointment_view(request):
    doctor_profile = DoctorFacade.get_doctor_profile(request.user.id)
    return render(request, 'doctor/doctor_appointment.html', {'doctor': doctor_profile})


@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_view_appointment_view(request):
    appointments_zip = DoctorFacade.get_appointments_with_patients(request.user.id)
    doctor_profile = DoctorFacade.get_doctor_profile(request.user.id)
    return render(request, 'doctor/doctor_view_appointment.html',
                  {'appointments': appointments_zip, 'doctor': doctor_profile})


@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_delete_appointment_view(request):
    appointments_zip = DoctorFacade.get_appointments_with_patients(request.user.id)
    doctor_profile = DoctorFacade.get_doctor_profile(request.user.id)
    return render(request, 'doctor/doctor_delete_appointment.html',
                  {'appointments': appointments_zip, 'doctor': doctor_profile})


@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def delete_appointment_view(request, pk):
    DoctorFacade.delete_appointment(pk)
    appointments_zip = DoctorFacade.get_appointments_with_patients(request.user.id)
    doctor_profile = DoctorFacade.get_doctor_profile(request.user.id)
    return render(request, 'doctor/doctor_delete_appointment.html',
                  {'appointments': appointments_zip, 'doctor': doctor_profile})