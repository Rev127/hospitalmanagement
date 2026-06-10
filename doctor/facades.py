from django.contrib.auth.models import User, Group
from django.db.models import Q
from patient.models import Patient
from hospital_admin.models import Appointment, PatientDischargeDetails
from .models import Doctor
from hospital.crypto_facade import CryptoFacade

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
        appointments = Appointment.objects.all().filter(status=True, doctorId=user.id).order_by('-id')
        patient_ids = [a.patientId for a in appointments]
        patients = Patient.objects.all().filter(status=True, user_id__in=patient_ids).order_by('-id')

        # Дешифруємо симптоми для списку на дашборді лікаря
        for p in patients:
            p.symptoms = CryptoFacade.decrypt(p.symptoms)

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
        patients = Patient.objects.all().filter(status=True, assignedDoctorId=user_id)
        for p in patients:
            p.symptoms = CryptoFacade.decrypt(p.symptoms)
        return patients

    @staticmethod
    def search_assigned_patients(user_id, query):
        """Крипто-захищений пошук пацієнтів у пам'яті сервера."""
        all_patients = Patient.objects.all().filter(status=True, assignedDoctorId=user_id)
        filtered_patients = []

        for p in all_patients:
            decrypted_symptoms = CryptoFacade.decrypt(p.symptoms)
            # Якщо запит збігається з розшифрованими симптомами або іменем
            if query.lower() in decrypted_symptoms.lower() or query.lower() in p.user.first_name.lower():
                p.symptoms = decrypted_symptoms  # повертаємо вже дешифрований об'єкт
                filtered_patients.append(p)
        return filtered_patients

    @staticmethod
    def get_discharged_patients(doctor_first_name):
        discharged = PatientDischargeDetails.objects.all().distinct().filter(assignedDoctorName=doctor_first_name)
        for d in discharged:
            d.symptoms = CryptoFacade.decrypt(d.symptoms)
        return discharged

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