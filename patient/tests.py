from django.test import TestCase
from django.contrib.auth.models import User, Group
from unittest.mock import MagicMock, patch
from datetime import date

from doctor.models import Doctor
from patient.models import Patient
from hospital_admin.models import Appointment, PatientDischargeDetails
from patient.facades import PatientFacade


class PatientFacadeTestSuite(TestCase):
    """Комплексний набір модульних тестів для верифікації бізнес-фасаду пацієнта."""

    def setUp(self):
        """Налаштування початкового середовища перед кожним тест-кейсом."""
        # Ініціалізація системних груп
        Group.objects.get_or_create(name='PATIENT')

        # Створюємо базового користувача-лікаря
        self.doc_user = User.objects.create_user(
            username='dr_smith', password='123', first_name='John', last_name='Smith'
        )
        # Створюємо профіль лікаря з усіма полями, які зчитує фасад пацієнта
        self.doctor = Doctor.objects.create(
            user=self.doc_user,
            mobile='0971112233',
            address='Київ, вул. Медична 5',
            department='Cardiology',
            status=True
        )

        # Створюємо базового користувача-пацієнта для тестів профілю та виписок
        self.pat_user = User.objects.create_user(
            username='patient_alex', password='123', first_name='Alex'
        )

    # =========================================================================
    # 1. ТЕСТИ РЕЄСТРАЦІЇ ТА АВТЕНТИФІКАЦІЇ
    # =========================================================================

    @patch('patient.facades.CryptoFacade')
    def test_register_new_patient_flow_and_group_assignment(self, mock_crypto):
        """Перевірка реєстрації пацієнта: хешування пароля, роль PATIENT та шифрування скарг."""
        mock_crypto.encrypt.return_value = "encrypted_symptoms_hash_123"

        # Мокаємо інстанси моделей та поведінку Django-форм
        user_mock_obj = User(username='new_patient_user', password='raw_password_999')
        patient_mock_obj = Patient(address='Львів', mobile='0630001122')

        user_form = MagicMock()
        user_form.save.return_value = user_mock_obj

        patient_form = MagicMock()
        patient_form.save.return_value = patient_mock_obj
        patient_form.cleaned_data = {'symptoms': 'Постійний кашель, задишка'}

        # Викликаємо бізнес-метод реєстрації
        registered_patient = PatientFacade.register_new_patient(user_form, patient_form, self.doctor.id)

        # Архітектурні перевірки результату
        self.assertEqual(registered_patient.user.username, 'new_patient_user')
        self.assertNotEqual(registered_patient.user.password, 'raw_password_999')  # Пароль захешовано
        self.assertTrue(registered_patient.user.groups.filter(name='PATIENT').exists())  # Групу прив'язано
        self.assertEqual(registered_patient.symptoms, "encrypted_symptoms_hash_123")  # Дані зашифровано
        mock_crypto.encrypt.assert_called_with('Постійний кашель, задишка')

    def test_get_patient_profile_retrieval(self):
        """Перевірка точного витягування сутності пацієнта за його ідентифікатором користувача."""
        test_patient = Patient.objects.create(user=self.pat_user, assignedDoctorId=self.doctor.id)

        profile = PatientFacade.get_patient_profile(self.pat_user.id)
        self.assertEqual(profile.id, test_patient.id)

    # =========================================================================
    # 2. ТЕСТИ РОБОЧОГО СТОЛУ ТА ДЕШИФРУВАННЯ (Dashboard Context)
    # =========================================================================

    @patch('patient.facades.CryptoFacade')
    def test_get_dashboard_context_transparent_decryption(self, mock_crypto):
        """Перевірка генерації контексту дашборду з автоматичним дешифруванням симптомів пацієнта."""
        mock_crypto.decrypt.return_value = "Біль у серці"

        test_patient = Patient.objects.create(
            user=self.pat_user,
            symptoms='secured_blob_data',
            assignedDoctorId=self.doc_user.id,
            admitDate=date.today()
        )

        context = PatientFacade.get_dashboard_context(self.pat_user.id)

        # Перевіряємо правильність мапування даних про лікаря та дешифрацію
        self.assertEqual(context['doctorMobile'], self.doctor.mobile)
        self.assertEqual(context['doctorDepartment'], self.doctor.department)
        self.assertEqual(context['symptoms'], "Біль у серці")
        mock_crypto.decrypt.assert_called_with('secured_blob_data')

    # =========================================================================
    # 3. ТЕСТИ ПОШУКУ ТА ФІЛЬТРАЦІЇ ЛІКАРІВ (Search & Filtering)
    # =========================================================================

    def test_get_active_doctors_filters_out_pending(self):
        """Перевірка вибірки лікарів: у список мають потрапляти ЛИШЕ верифіковані (status=True)."""
        inactive_user = User.objects.create_user(username='pending_doc')
        Doctor.objects.create(user=inactive_user, status=False)  # Неактивний лікар

        active_list = PatientFacade.get_active_doctors()
        self.assertEqual(active_list.count(), 1)  # Тільки self.doctor з setUp

    def test_search_doctors_by_department_and_name(self):
        """Перевірка роботи Q-фільтра пошуку за назвою відділення або ім'ям лікаря."""
        # Пошук за релевантним відділенням (Cardiology)
        res_dept = PatientFacade.search_doctors(query="cardio")
        self.assertEqual(res_dept.count(), 1)

        # Пошук за ім'ям (John)
        res_name = PatientFacade.search_doctors(query="jOhN")
        self.assertEqual(res_name.count(), 1)

        # Пошук за неіснуючим критерієм
        res_empty = PatientFacade.search_doctors(query="Neurology")
        self.assertEqual(res_empty.count(), 0)

    # =========================================================================
    # 4. ВЗАЄМОДІЯ З ПРИЙОМАМИ ТА ВИПИСКАМИ (Appointments & Discharges)
    # =========================================================================

    def test_book_appointment_creation(self):
        """Перевірка формування нової заявки на прийом та автоматичного підтягування імен."""
        app_mock_obj = Appointment()
        app_form = MagicMock()
        app_form.save.return_value = app_mock_obj

        new_appointment = PatientFacade.book_appointment(
            user=self.pat_user, appointment_form=app_form, doctor_id=self.doc_user.id
        )

        # Перевіряємо заповнення денормалізованих полів імен для фронтенду
        self.assertEqual(new_appointment.doctorName, 'John')
        self.assertEqual(new_appointment.patientName, 'Alex')
        self.assertFalse(new_appointment.status)  # Заявка повинна очікувати модерації адміна

    def test_get_discharge_details_context_not_discharged_yet(self):
        """Перевірка поведінки методу, якщо пацієнт ще лікується і запису про виписку немає."""
        Patient.objects.create(user=self.pat_user, assignedDoctorId=self.doc_user.id)

        ctx = PatientFacade.get_discharge_details_context(self.pat_user.id)
        self.assertFalse(ctx['is_discharged'])