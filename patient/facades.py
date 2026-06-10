from django.contrib.auth.models import User, Group
from django.db.models import Q
from doctor.models import Doctor
from hospital_admin.models import Appointment, PatientDischargeDetails
from .models import Patient
from hospital.crypto_facade import CryptoFacade


class PatientFacade:

    @staticmethod
    def register_new_patient(user_form, patient_form, assigned_doctor_id):
        user = user_form.save(commit=False)
        user.set_password(user.password)
        user.save()

        patient = patient_form.save(commit=False)
        patient.user = user
        patient.assignedDoctorId = assigned_doctor_id

        # --- ШИФРУВАННЯ ПЕРЕД ЗАПИСОМ В MySQL ---
        patient.symptoms = CryptoFacade.encrypt(patient_form.cleaned_data['symptoms'])

        patient.save()

        my_patient_group = Group.objects.get_or_create(name='ADMIN' if False else 'PATIENT')  # безпечний груп-сет
        my_patient_group[0].user_set.add(user)
        return patient

    @staticmethod
    def get_dashboard_context(user_id):
        patient = Patient.objects.get(user_id=user_id)
        doctor = Doctor.objects.get(user_id=patient.assignedDoctorId)

        return {
            'patient': patient,
            'doctorName': doctor.get_name,
            'doctorMobile': doctor.mobile,
            'doctorAddress': doctor.address,
            # --- ДЕШИФРУВАННЯ ПЕРЕД СТОРІНКОЮ ЮЗЕРА ---
            'symptoms': CryptoFacade.decrypt(patient.symptoms),
            'doctorDepartment': doctor.department,
            'admitDate': patient.admitDate,
        }

    @staticmethod
    def get_patient_profile(user_id):
        """Повертає сутність пацієнта за його user_id (для відображення сайдбару/аватарок)."""
        return Patient.objects.get(user_id=user_id)

    @staticmethod
    def book_appointment(user, appointment_form, doctor_id):
        """Реалізує логіку формування та збереження заявки на прийом."""
        appointment = appointment_form.save(commit=False)
        appointment.doctorId = doctor_id
        appointment.patientId = user.id
        appointment.doctorName = User.objects.get(id=doctor_id).first_name
        appointment.patientName = user.first_name
        appointment.status = False
        appointment.save()
        return appointment

    @staticmethod
    def get_active_doctors():
        """Повертає список усіх верифікованих лікарів системи."""
        return Doctor.objects.all().filter(status=True)

    @staticmethod
    def search_doctors(query):
        """Шукає лікарів за спеціалізацією або іменем."""
        return Doctor.objects.all().filter(status=True).filter(
            Q(department__icontains=query) | Q(user__first_name__icontains=query)
        )

    @staticmethod
    def get_patient_appointments(user_id):
        """Отримує всі записи на прийом конкретного пацієнта."""
        return Appointment.objects.all().filter(patientId=user_id)

    @staticmethod
    def get_discharge_details_context(user_id):
        patient = Patient.objects.get(user_id=user_id)
        discharge_details = PatientDischargeDetails.objects.all().filter(patientId=patient.id).order_by('-id')[:1]

        if discharge_details:
            return {
                'is_discharged': True,
                'patient': patient,
                'patientId': patient.id,
                'patientName': patient.get_name,
                'assignedDoctorName': discharge_details[0].assignedDoctorName,
                'address': patient.address,
                'mobile': patient.mobile,
                # --- ДЕШИФРУВАННЯ ---
                'symptoms': CryptoFacade.decrypt(discharge_details[0].symptoms),
                'admitDate': patient.admitDate,
                'releaseDate': discharge_details[0].releaseDate,
                'daySpent': discharge_details[0].daySpent,
                'medicineCost': discharge_details[0].medicineCost,
                'roomCharge': discharge_details[0].roomCharge,
                'doctorFee': discharge_details[0].doctorFee,
                'OtherCharge': discharge_details[0].OtherCharge,
                'total': discharge_details[0].total,
            }
        return {'is_discharged': False, 'patient': patient, 'patientId': user_id}