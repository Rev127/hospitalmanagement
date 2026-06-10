from django.contrib import admin
from .models import Appointment, PatientDischargeDetails

admin.site.register(Appointment)
admin.site.register(PatientDischargeDetails)