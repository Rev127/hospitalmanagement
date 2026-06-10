from django import forms
from django.contrib.auth.models import User
from doctor.models import Doctor
from hospital_admin.models import Appointment
from .models import Patient

class PatientUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'password']
        widgets = {'password': forms.PasswordInput()}

class PatientForm(forms.ModelForm):
    assignedDoctorId = forms.ModelChoiceField(queryset=Doctor.objects.all().filter(status=True), empty_label="Name and Department", to_field_name="user_id")
    class Meta:
        model = Patient
        fields = ['address', 'mobile', 'status', 'symptoms', 'profile_pic']

class PatientAppointmentForm(forms.ModelForm):
    doctorId = forms.ModelChoiceField(queryset=Doctor.objects.all().filter(status=True), empty_label="Doctor Name and Department", to_field_name="user_id")
    class Meta:
        model = Appointment
        fields = ['description', 'status']