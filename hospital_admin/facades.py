from django.contrib.auth.models import User, Group
from datetime import date
from doctor.models import Doctor
from patient.models import Patient
from .models import Appointment, PatientDischargeDetails
from hospital.crypto_facade import CryptoFacade


class AdminFacade:

    @staticmethod
    def register_admin(form):
        """Реєстрація адміністратора, хешування пароля та додавання до групи."""
        user = form.save()
        user.set_password(user.password)
        user.save()
        my_admin_group = Group.objects.get_or_create(name='ADMIN')
        my_admin_group[0].user_set.add(user)
        return user

    @staticmethod
    def get_dashboard_context():
        """Збір усієї агрегованої аналітики та лічильників для головного екрана."""
        doctors = Doctor.objects.all().order_by('-id')
        patients = list(Patient.objects.all().order_by('-id'))

        # --- ДЕШИФРУЄМО СИМПТОМИ ДЛЯ КОЖНОГО ПАЦІЄНТА В СПИСКУ ДАШБОРДУ ---
        for p in patients:
            p.symptoms = CryptoFacade.decrypt(p.symptoms)

        return {
            'doctors': doctors,
            'patients': patients,
            'doctorcount': Doctor.objects.all().filter(status=True).count(),
            'pendingdoctorcount': Doctor.objects.all().filter(status=False).count(),
            'patientcount': Patient.objects.all().filter(status=True).count(),
            'pendingpatientcount': Patient.objects.all().filter(status=False).count(),
            'appointmentcount': Appointment.objects.all().filter(status=True).count(),
            'pendingappointmentcount': Appointment.objects.all().filter(status=False).count(),
        }

    # --- УПРАВЛІННЯ ЛІКАРЯМИ ---
    @staticmethod
    def get_approved_doctors():
        return Doctor.objects.all().filter(status=True)

    @staticmethod
    def get_pending_doctors():
        return Doctor.objects.all().filter(status=False)

    @staticmethod
    def delete_doctor(doctor_id):
        doctor = Doctor.objects.get(id=doctor_id)
        User.objects.get(id=doctor.user_id).delete()
        doctor.delete()

    @staticmethod
    def save_doctor(user_form, doctor_form, user_instance=None, doctor_instance=None):
        """Універсальний метод для створення або оновлення лікаря адміністратором."""
        user = user_form.save(commit=False)
        if not user_instance:
            user.set_password(user.password)
        user.save()

        doctor = doctor_form.save(commit=False)
        if not doctor_instance:
            doctor.user = user
        doctor.status = True
        doctor.save()

        if not user_instance:
            my_doctor_group = Group.objects.get_or_create(name='DOCTOR')
            my_doctor_group[0].user_set.add(user)
        return doctor

    @staticmethod
    def approve_doctor(doctor_id):
        doctor = Doctor.objects.get(id=doctor_id)
        doctor.status = True
        doctor.save()

    # --- УПРАВЛІННЯ ПАЦІЄНТАМИ (ДООПРАЦЬОВАНО ДЛЯ ДЕШИФРУВАННЯ) ---
    @staticmethod
    def get_approved_patients():
        """Повертає список затверджених пацієнтів із розшифрованими симптомами."""
        patients = list(Patient.objects.all().filter(status=True))
        for p in patients:
            p.symptoms = CryptoFacade.decrypt(p.symptoms)
        return patients

    @staticmethod
    def get_pending_patients():
        """Повертає список пацієнтів на модерацію із розшифрованими симптомами."""
        patients = list(Patient.objects.all().filter(status=False))
        for p in patients:
            p.symptoms = CryptoFacade.decrypt(p.symptoms)
        return patients

    @staticmethod
    def delete_patient(patient_id):
        patient = Patient.objects.get(id=patient_id)
        User.objects.get(id=patient.user_id).delete()
        patient.delete()

    @staticmethod
    def save_patient(user_form, patient_form, assigned_doctor_id, user_instance=None, patient_instance=None):
        """Універсальний метод для створення або оновлення пацієнта адміністратором."""
        user = user_form.save(commit=False)
        if not user_instance:
            user.set_password(user.password)
        user.save()

        patient = patient_form.save(commit=False)
        if not patient_instance:
            patient.user = user
        patient.status = True
        patient.assignedDoctorId = assigned_doctor_id

        if 'symptoms' in patient_form.cleaned_data:
            patient.symptoms = CryptoFacade.encrypt(patient_form.cleaned_data['symptoms'])

        patient.save()

        if not user_instance:
            my_patient_group = Group.objects.get_or_create(name='PATIENT')
            my_patient_group[0].user_set.add(user)
        return patient

    @staticmethod
    def approve_patient(patient_id):
        doctor = Doctor.objects.get(id=pk)
        doctor.status = True
        doctor.save()

    # --- ВИПИСКА ТА ФІНАНСОВІ РОЗРАХУНКИ (ДООПРАЦЬОВАНО ДЛЯ ДЕШИФРУВАННЯ) ---
    @staticmethod
    def get_discharge_initial_context(patient_id):
        patient = Patient.objects.get(id=patient_id)
        days = (date.today() - patient.admitDate)
        d = days.days if days.days > 0 else 1
        assigned_doctor_user = User.objects.all().filter(id=patient.assignedDoctorId).first()
        return {
            'patientId': patient_id,
            'name': patient.get_name,
            'mobile': patient.mobile,
            'address': patient.address,
            'symptoms': CryptoFacade.decrypt(patient.symptoms),
            'admitDate': patient.admitDate,
            'todayDate': date.today(), 'day': d,
            'assignedDoctorName': assigned_doctor_user.first_name if assigned_doctor_user else "Не призначено",
        }

    @staticmethod
    def process_patient_discharge(patient_id, context, post_data):
        d = context['day']

        pDD = PatientDischargeDetails()
        pDD.patientId = patient_id
        pDD.patientName = context['name']
        pDD.assignedDoctorName = context['assignedDoctorName']
        pDD.address = context['address']
        pDD.mobile = context['mobile']

        # Шифруємо симптоми перед фіксацією в архівній таблиці виписок
        pDD.symptoms = CryptoFacade.encrypt(context['symptoms'])

        pDD.admitDate = context['admitDate']
        pDD.releaseDate = date.today()
        pDD.daySpent = int(d)
        pDD.medicineCost = int(post_data['medicineCost'])
        pDD.roomCharge = int(post_data['roomCharge']) * int(d)
        pDD.doctorFee = int(post_data['doctorFee'])
        pDD.OtherCharge = int(post_data['OtherCharge'])
        pDD.total = pDD.roomCharge + pDD.doctorFee + pDD.medicineCost + pDD.OtherCharge
        pDD.save()

        context.update({
            'roomCharge': pDD.roomCharge, 'doctorFee': pDD.doctorFee,
            'medicineCost': pDD.medicineCost, 'OtherCharge': pDD.OtherCharge, 'total': pDD.total
        })
        return context

    @staticmethod
    def get_latest_discharge_bill(patient_id):
        """Повертає останній чек виписки із розшифрованими симптомами для PDF-документа."""
        bill = PatientDischargeDetails.objects.all().filter(patientId=patient_id).order_by('-id').first()
        if bill:
            bill.symptoms = CryptoFacade.decrypt(bill.symptoms)
        return bill

    # --- ЗАПИСИ НА ПРИЙОМ (APPOINTMENTS) ---
    @staticmethod
    def get_approved_appointments():
        return Appointment.objects.all().filter(status=True)

    @staticmethod
    def get_pending_appointments():
        return Appointment.objects.all().filter(status=False)

    @staticmethod
    def create_appointment_by_admin(appointment_form, doctor_id, patient_id):
        appointment = appointment_form.save(commit=False)
        appointment.doctorId = doctor_id
        appointment.patientId = patient_id
        appointment.doctorName = User.objects.get(id=doctor_id).first_name
        appointment.patientName = User.objects.get(id=patient_id).first_name
        appointment.status = True
        appointment.save()
        return appointment

    @staticmethod
    def approve_appointment(appointment_id):
        appointment = Appointment.objects.get(id=appointment_id)
        appointment.status = True
        appointment.save()

    @staticmethod
    def delete_appointment(appointment_id):
        Appointment.objects.get(id=appointment_id).delete()

    @staticmethod
    def get_patient_for_update(patient_id):
        """Ізолює views від прямого доступу до моделей та дешифрування."""
        patient = Patient.objects.get(id=patient_id)
        user = User.objects.get(id=patient.user_id)

        # Дешифруємо дані всередині фасаду
        patient.symptoms = CryptoFacade.decrypt(patient.symptoms)

        return user, patient