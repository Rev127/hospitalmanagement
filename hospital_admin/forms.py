from django import forms
from django.contrib.auth.models import User
from .models import Appointment


class AdminSigupForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'password']
        widgets = {
            'password': forms.PasswordInput()
        }


class AppointmentForm(forms.ModelForm):
    from doctor.models import Doctor
    from patient.models import Patient

    doctorId = forms.ModelChoiceField(queryset=Doctor.objects.all().filter(status=True),
                                      empty_label="Doctor Name and Department", to_field_name="user_id")
    patientId = forms.ModelChoiceField(queryset=Patient.objects.all().filter(status=True),
                                       empty_label="Patient Name and Symptoms", to_field_name="user_id")

    class Meta:
        model = Appointment
        fields = ['description', 'status']