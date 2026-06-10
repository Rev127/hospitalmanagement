from django.contrib.auth.models import User, Group
from django.db.models import Q
from patient.models import Patient
from hospital_admin.models import Appointment, PatientDischargeDetails
from .models import Doctor


class DoctorFacade:

    @staticmethod
    def register_new_doctor(user_form, doctor_form):
        """Інкапсулює повний процес реєстрації лікаря та прив'язку до рольової групи."""
        user = user_form.save(commit=False)
        user.set_password(user.password)
        user.save()

        doctor = doctor_form.save(commit=False)
        doctor.user = user
        doctor.save()

        my_doctor_group = Group.objects.get_or_create(name='DOCTOR')
        my_doctor_group[0].user_set.add(user)
        return doctor

    @staticmethod
    def get_dashboard_context(user):
        """Формує аналітичні картки та списки прийомів для головного екрана лікаря."""
        appointments = Appointment.objects.all().filter(status=True, doctorId=user.id).order_by('-id')
        patient_ids = [a.patientId for a in appointments]
        patients = Patient.objects.all().filter(status=True, user_id__in=patient_ids).order_by('-id')

        return {
            'patientcount': Patient.objects.all().filter(status=True, assignedDoctorId=user.id).count(),
            'appointmentcount': appointments.count(),
            'patientdischarged': PatientDischargeDetails.objects.all().distinct().filter(
                assignedDoctorName=user.first_name).count(),
            'appointments': zip(appointments, patients),
            'doctor': Doctor.objects.get(user_id=user.id),
        }

    @staticmethod
    def get_doctor_profile(user_id):
        """Повертає об'єкт профілю лікаря за його ідентифікатором користувача."""
        return Doctor.objects.get(user_id=user_id)

    @staticmethod
    def get_assigned_patients(user_id):
        """Отримує список усіх активних пацієнтів лікаря."""
        return Patient.objects.all().filter(status=True, assignedDoctorId=user_id)

    @staticmethod
    def search_assigned_patients(user_id, query):
        """Здійснює пошук серед пацієнтів лікаря за симптомами або іменем."""
        return Patient.objects.all().filter(status=True, assignedDoctorId=user_id).filter(
            Q(symptoms__icontains=query) | Q(user__first_name__icontains=query)
        )

    @staticmethod
    def get_discharged_patients(doctor_first_name):
        """Повертає історичні записи виписаних пацієнтів, у яких лікарем був поточний користувач."""
        return PatientDischargeDetails.objects.all().distinct().filter(assignedDoctorName=doctor_first_name)

    @staticmethod
    def get_appointments_with_patients(user_id):
        """Збирає та компонує активні прийоми з відповідними сутностями пацієнтів."""
        appointments = Appointment.objects.all().filter(status=True, doctorId=user_id)
        patient_ids = [a.patientId for a in appointments]
        patients = Patient.objects.all().filter(status=True, user_id__in=patient_ids)
        return zip(appointments, patients)

    @staticmethod
    def delete_appointment(appointment_id):
        """Видаляє запис про прийом із бази даних системи (закриття прийому лікарем)."""
        Appointment.objects.get(id=appointment_id).delete()