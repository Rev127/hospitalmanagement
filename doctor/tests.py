from django.test import TestCase
from django.contrib.auth.models import User, Group
from unittest.mock import MagicMock, patch
from datetime import date  # Імпортуємо модуль дат для бази даних

from doctor.models import Doctor
from patient.models import Patient
from hospital_admin.models import Appointment, PatientDischargeDetails
from doctor.facades import DoctorFacade


class DoctorFacadeTestSuite(TestCase):
    """Комплексний набір модульних тестів для верифікації бізнес-фасаду лікаря (DoctorFacade)."""

    def setUp(self):
        """Налаштування тестового середовища перед кожним тест-кейсом."""
        # Обов'язкова системна група
        self.doctor_group, _ = Group.objects.get_or_create(name='DOCTOR')

        # Створюємо базового користувача-лікаря для авторизованого контексту
        self.doc_user = User.objects.create_user(
            username='g_house', password='password_123', first_name='Gregory', last_name='House'
        )
        self.doctor_profile = Doctor.objects.create(user=self.doc_user, status=True)

        # Створюємо користувача-пацієнта для зв'язків
        self.patient_user = User.objects.create_user(
            username='john_doe', password='password_123', first_name='John', last_name='Doe'
        )

    # =========================================================================
    # 1. ТЕСТИ РЕЄСТРАЦІЇ ТА ПРОФІЛЮ (Account Management)
    # =========================================================================

    def test_register_new_doctor_flow(self):
        """Перевірка повного циклу реєстрації лікаря: шифрування пароля та прив'язка групи."""
        mock_user = User(username='new_surgeon', password='raw_password_777')
        mock_doctor = Doctor()

        user_form = MagicMock()
        user_form.save.return_value = mock_user
        doctor_form = MagicMock()
        doctor_form.save.return_value = mock_doctor

        registered_doctor = DoctorFacade.register_new_doctor(user_form, doctor_form)

        # Перевіряємо архітектурні інваріанти
        self.assertEqual(registered_doctor.user.username, 'new_surgeon')
        self.assertNotEqual(registered_doctor.user.password, 'raw_password_777')
        self.assertTrue(registered_doctor.user.groups.filter(name='DOCTOR').exists())

    def test_get_doctor_profile_by_user_id(self):
        """Перевірка точного витягування сутності профілю лікаря за його user_id."""
        profile = DoctorFacade.get_doctor_profile(self.doc_user.id)
        self.assertEqual(profile.id, self.doctor_profile.id)
        self.assertEqual(profile.user.username, 'g_house')

    # =========================================================================
    # 2. ТЕСТИ ДАШБОРДУ ТА МЕДИЧНИХ ДАНИХ (Dashboard & Querysets)
    # =========================================================================

    @patch('doctor.facades.CryptoFacade')
    def test_get_assigned_patients_transparent_decryption(self, mock_crypto):
        """Перевірка, що метод повертає список пацієнтів лікаря з уже розшифрованими картами."""
        mock_crypto.decrypt.return_value = "Стабільний стан"
        Patient.objects.create(
            user=self.patient_user, symptoms='encrypted_symptoms_data', status=True, assignedDoctorId=self.doc_user.id
        )

        assigned_patients = DoctorFacade.get_assigned_patients(self.doc_user.id)

        self.assertEqual(assigned_patients[0].symptoms, "Стабільний стан")
        mock_crypto.decrypt.assert_called_once_with('encrypted_symptoms_data')

    # =========================================================================
    # 3. ТЕСТИ КРИПТО-ЗАХИЩЕНОГО ПОШУКУ (Secure In-Memory Search)
    # =========================================================================

    @patch('doctor.facades.CryptoFacade')  # Виправлено шлях до моку!
    def test_search_assigned_patients_by_symptoms_match(self, mock_crypto):
        """Тестування In-Memory пошуку: успішний збіг за дешифрованим медичним симптомом."""
        mock_crypto.decrypt.return_value = "Перелом лівої ноги"
        Patient.objects.create(
            user=self.patient_user, symptoms='crypto_blob_1', status=True, assignedDoctorId=self.doc_user.id
        )

        # Шукаємо слово "перелом" (в БД лежить зашифрований рядок 'crypto_blob_1')
        results = DoctorFacade.search_assigned_patients(self.doc_user.id, query="ПЕРЕЛОМ")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].symptoms, "Перелом лівої ноги")

    @patch('doctor.facades.CryptoFacade')  # Виправлено шлях до моку!
    def test_search_assigned_patients_by_name_match(self, mock_crypto):
        """Тестування In-Memory пошуку: успішний збіг за іменем пацієнта (John)."""
        mock_crypto.decrypt.return_value = "Здоровий"
        Patient.objects.create(
            user=self.patient_user, symptoms='crypto_blob_2', status=True, assignedDoctorId=self.doc_user.id
        )

        # Шукаємо за іменем користувача
        results = DoctorFacade.search_assigned_patients(self.doc_user.id, query="joHn")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].user.first_name, "John")

    @patch('doctor.facades.CryptoFacade')  # Виправлено шлях до моку!
    def test_search_assigned_patients_no_results(self, mock_crypto):
        """Тестування In-Memory пошуку: повернення порожнього списку, якщо збігів немає."""
        mock_crypto.decrypt.return_value = "Застуда"
        Patient.objects.create(
            user=self.patient_user, symptoms='crypto_blob_3', status=True, assignedDoctorId=self.doc_user.id
        )

        results = DoctorFacade.search_assigned_patients(self.doc_user.id, query="Гепатит")
        self.assertEqual(len(results), 0)

    # =========================================================================
    # 4. УПРАВЛІННЯ ПРИЙОМАМИ (Appointment Workflows)
    # =========================================================================

    def test_delete_appointment_action(self):
        """Перевірка успішного видалення прийому."""
        app = Appointment.objects.create(
            patientId=self.patient_user.id, doctorId=self.doc_user.id, status=True
        )

        DoctorFacade.delete_appointment(app.id)
        self.assertFalse(Appointment.objects.filter(id=app.id).exists())