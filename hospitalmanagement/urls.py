"""

Developed By : sumit kumar
facebook : fb.com/sumit.luv
Youtube :youtube.com/lazycoders


"""

from django.contrib import admin
from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView

from django.contrib import admin
from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView

# Імпортуємо views з кожного пакета окремо (тепер hospital_admin)
from hospital import views as hospital_views
from hospital_admin import views as admin_views
from doctor import views as doctor_views
from patient import views as patient_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', hospital_views.home_view, name=''),

    path('aboutus', hospital_views.aboutus_view),
    path('contactus', hospital_views.contactus_view),

    path('adminclick', hospital_views.adminclick_view),
    path('doctorclick', hospital_views.doctorclick_view),
    path('patientclick', hospital_views.patientclick_view),

    # Маршрути реєстрації (Signup)
    path('adminsignup', admin_views.admin_signup_view),
    path('doctorsignup', doctor_views.doctor_signup_view, name='doctorsignup'),
    path('patientsignup', patient_views.patient_signup_view),

    path('adminlogin', LoginView.as_view(template_name='hospital/adminlogin.html')),
    path('doctorlogin', LoginView.as_view(template_name='hospital/doctorlogin.html')),
    path('patientlogin', LoginView.as_view(template_name='hospital/patientlogin.html')),

    path('afterlogin', hospital_views.afterlogin_view, name='afterlogin'),
    path('logout', LogoutView.as_view(template_name='hospital/index.html'), name='logout'),

    # ------------- АДМІНІСТРАТОР (hospital_admin)
    path('admin-dashboard', admin_views.admin_dashboard_view, name='admin-dashboard'),
    path('admin-doctor', admin_views.admin_doctor_view, name='admin-doctor'),
    path('admin-view-doctor', admin_views.admin_view_doctor_view, name='admin-view-doctor'),
    path('delete-doctor-from-hospital/<int:pk>', admin_views.delete_doctor_from_hospital_view,
         name='delete-doctor-from-hospital'),
    path('update-doctor/<int:pk>', admin_views.update_doctor_view, name='update-doctor'),
    path('admin-add-doctor', admin_views.admin_add_doctor_view, name='admin-add-doctor'),
    path('admin-approve-doctor', admin_views.admin_approve_doctor_view, name='admin-approve-doctor'),
    path('approve-doctor/<int:pk>', admin_views.approve_doctor_view, name='approve-doctor'),
    path('reject-doctor/<int:pk>', admin_views.reject_doctor_view, name='reject-doctor'),
    path('admin-view-doctor-specialisation', admin_views.admin_view_doctor_specialisation_view,
         name='admin-view-doctor-specialisation'),

    path('admin-patient', admin_views.admin_patient_view, name='admin-patient'),
    path('admin-view-patient', admin_views.admin_view_patient_view, name='admin-view-patient'),
    path('delete-patient-from-hospital/<int:pk>', admin_views.delete_patient_from_hospital_view,
         name='delete-patient-from-hospital'),
    path('update-patient/<int:pk>', admin_views.update_patient_view, name='update-patient'),
    path('admin-add-patient', admin_views.admin_add_patient_view, name='admin-add-patient'),
    path('admin-approve-patient', admin_views.admin_approve_patient_view, name='admin-approve-patient'),
    path('approve-patient/<int:pk>', admin_views.approve_patient_view, name='approve-patient'),
    path('reject-patient/<int:pk>', admin_views.reject_patient_view, name='reject-patient'),
    path('admin-discharge-patient', admin_views.admin_discharge_patient_view, name='admin-discharge-patient'),
    path('discharge-patient/<int:pk>', admin_views.discharge_patient_view, name='discharge-patient'),
    path('download-pdf/<int:pk>', admin_views.download_pdf_view, name='download-pdf'),

    path('admin-appointment', admin_views.admin_appointment_view, name='admin-appointment'),
    path('admin-view-appointment', admin_views.admin_view_appointment_view, name='admin-view-appointment'),
    path('admin-add-appointment', admin_views.admin_add_appointment_view, name='admin-add-appointment'),
    path('admin-approve-appointment', admin_views.admin_approve_appointment_view, name='admin-approve-appointment'),
    path('approve-appointment/<int:pk>', admin_views.approve_appointment_view, name='approve-appointment'),
    path('reject-appointment/<int:pk>', admin_views.reject_appointment_view, name='reject-appointment'),
]

# --------- ЛІКАР (doctor)
urlpatterns += [
    path('doctor-dashboard', doctor_views.doctor_dashboard_view, name='doctor-dashboard'),
    path('search', doctor_views.search_view, name='search'),
    path('doctor-patient', doctor_views.doctor_patient_view, name='doctor-patient'),
    path('doctor-view-patient', doctor_views.doctor_view_patient_view, name='doctor-view-patient'),
    path('doctor-view-discharge-patient', doctor_views.doctor_view_discharge_patient_view,
         name='doctor-view-discharge-patient'),
    path('doctor-appointment', doctor_views.doctor_appointment_view, name='doctor-appointment'),
    path('doctor-view-appointment', doctor_views.doctor_view_appointment_view, name='doctor-view-appointment'),
    path('doctor-delete-appointment', doctor_views.doctor_delete_appointment_view, name='doctor-delete-appointment'),
    path('delete-appointment/<int:pk>', doctor_views.delete_appointment_view, name='delete-appointment'),
]

# --------- ПАЦІЄНТ (patient)
urlpatterns += [
    path('patient-dashboard', patient_views.patient_dashboard_view, name='patient-dashboard'),
    path('patient-appointment', patient_views.patient_appointment_view, name='patient-appointment'),
    path('patient-book-appointment', patient_views.patient_book_appointment_view, name='patient-book-appointment'),
    path('patient-view-appointment', patient_views.patient_view_appointment_view, name='patient-view-appointment'),
    path('patient-view-doctor', patient_views.patient_view_doctor_view, name='patient-view-doctor'),
    path('searchdoctor', patient_views.search_doctor_view, name='searchdoctor'),
    path('patient-discharge', patient_views.patient_discharge_view, name='patient-discharge'),
]

#Developed By : sumit kumar
#facebook : fb.com/sumit.luv
#Youtube :youtube.com/lazycoders
