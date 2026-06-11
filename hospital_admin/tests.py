from django.test import TestCase
from django.contrib.auth.models import User, Group
from datetime import date
from unittest.mock import MagicMock, patch

from doctor.models import Doctor
from patient.models import Patient
from hospital_admin.models import Appointment, PatientDischargeDetails
from hospital_admin.facades import AdminFacade


class AdminFacadeTestSuite(TestCase):
    """Комплексний набір модульних тестів для верифікації бізнес-фасаду адміністратора."""

    def setUp(self):
        """Налаштування початкового середовища перед кожним тестом."""
        # Створюємо обов'язкові системні групи доступу
        self.admin_group, _ = Group.objects.get_or_create(name='ADMIN')
        self.doctor_group, _ = Group.objects.get_or_create(name='DOCTOR')
        self.patient_group, _ = Group.objects.get_or_create(name='PATIENT')

        # Створюємо базового лікаря для тестів зв'язків
        self.doc_user = User.objects.create_user(username='dr_house', password='123', first_name='Gregory')
        self.doctor = Doctor.objects.create(user=self.doc_user, status=True)

    # =========================================================================
    # 1. ТЕСТИ АВТЕНТИФІКАЦІЇ ТА АНАЛІТИКИ (Dashboard)
    # =========================================================================

    def test_register_admin_flow(self):
        """Перевірка реєстрації адміна: створення, хешування пароля та додавання в групу."""
        # Мокаємо форму користувача
        mock_user = User(username='super_admin', password='raw_password_xyz')
        mock_form = MagicMock()
        mock_form.save.return_value = mock_user

        registered_user = AdminFacade.register_admin(mock_form)

        # Перевірки
        self.assertEqual(registered_user.username, 'super_admin')
        self.assertNotEqual(registered_user.password, 'raw_password_xyz')  # Пароль захешовано
        self.assertTrue(registered_user.groups.filter(name='ADMIN').exists())  # Додано в групу

    @patch('hospital_admin.facades.CryptoFacade')
    def test_get_dashboard_context_aggregation(self, mock_crypto):
        """Перевірка збору аналітики та прозорого дешифрування симптомів на дашборді."""
        mock_crypto.decrypt.return_value = "Розшифрований симптом"

        # Створюємо тестового пацієнта
        pat_user = User.objects.create_user(username='patient_1')
        Patient.objects.create(user=pat_user, symptoms='encrypted_data_blob', status=False,
                               assignedDoctorId=self.doc_user.id)

        context = AdminFacade.get_dashboard_context()

        # Тестуємо лічильники та масив даних
        self.assertEqual(context['pendingpatientcount'], 1)
        self.assertEqual(context['doctorcount'], 1)
        self.assertEqual(context['patients'][0].symptoms, "Розшифрований симптом")
        mock_crypto.decrypt.assert_called_with('encrypted_data_blob')

    # =========================================================================
    # 2. ТЕСТИ УПРАВЛІННЯ ЛІКАРЯМИ (Doctor CRUD)
    # =========================================================================

    def test_approve_doctor_action(self):
        """Перевірка активації профілю лікаря адміном."""
        u = User.objects.create_user(username='new_doc')
        doc = Doctor.objects.create(user=u, status=False)

        AdminFacade.approve_doctor(doc.id)
        self.assertTrue(Doctor.objects.get(id=doc.id).status)

    def test_delete_doctor_cascading(self):
        """Перевірка, що видалення лікаря каскадно видаляє і його системного User."""
        u = User.objects.create_user(username='deleted_doc')
        doc = Doctor.objects.create(user=u, status=True)

        AdminFacade.delete_doctor(doc.id)

        self.assertFalse(Doctor.objects.filter(id=doc.id).exists())
        self.assertFalse(User.objects.filter(id=u.id).exists())

    def test_save_doctor_creation_flow(self):
        """Перевірка створення нового лікаря з автоматичним паролем та групою."""
        user_mock_obj = User(username='fresh_doc', password='password1')
        doc_mock_obj = Doctor()

        user_form = MagicMock()
        user_form.save.return_value = user_mock_obj
        doc_form = MagicMock()
        doc_form.save.return_value = doc_mock_obj

        saved_doc = AdminFacade.save_doctor(user_form, doc_form)

        self.assertTrue(saved_doc.status)
        self.assertEqual(saved_doc.user.username, 'fresh_doc')
        self.assertTrue(saved_doc.user.groups.filter(name='DOCTOR').exists())

    # =========================================================================
    # 3. ТЕСТИ УПРАВЛІННЯ ПАЦІЄНТАМИ (Patient CRUD)
    # =========================================================================

    def test_approve_patient_action(self):
        """Перевірка активації статусу пацієнта (попри копіпаст змінної 'doctor')."""
        u = User.objects.create_user(username='p_user')
        pat = Patient.objects.create(user=u, status=False, assignedDoctorId=self.doc_user.id)

        AdminFacade.approve_patient(pat.id)
        self.assertTrue(Patient.objects.get(id=pat.id).status)

    @patch('hospital_admin.facades.CryptoFacade')
    def test_save_patient_with_encryption(self, mock_crypto):
        """Перевірка, що при збереженні пацієнта симптоми примусово шифруються."""
        mock_crypto.encrypt.return_value = "secured_hash_999"

        user_mock_obj = User(username='patient_joe', password='password1')
        patient_mock_obj = Patient()

        user_form = MagicMock()
        user_form.save.return_value = user_mock_obj

        patient_form = MagicMock()
        patient_form.save.return_value = patient_mock_obj
        patient_form.cleaned_data = {'symptoms': 'Постійний нежить і задишка'}

        saved_patient = AdminFacade.save_patient(user_form, patient_form, assigned_doctor_id=self.doctor.id)

        self.assertEqual(saved_patient.symptoms, "secured_hash_999")
        mock_crypto.encrypt.assert_called_with('Постійний нежить і задишка')

    # =========================================================================
    # 4. ТЕСТИ ВИПИСКИ ТА РОЗРАХУНКІВ (Discharge Workflows)
    # =========================================================================

    @patch('hospital_admin.facades.CryptoFacade')
    def test_get_discharge_initial_context(self, mock_crypto):
        """Перевірка підготовки фінансового контексту та дешифрування для чеку виписки."""
        mock_crypto.decrypt.return_value = "Алергія"
        u = User.objects.create_user(username='discharge_patient')
        pat = Patient.objects.create(
            user=u, symptoms='secret_blob', admitDate=date.today(), assignedDoctorId=self.doc_user.id
        )

        ctx = AdminFacade.get_discharge_initial_context(pat.id)

        self.assertEqual(ctx['symptoms'], "Алергія")
        self.assertEqual(ctx['assignedDoctorName'], "Gregory")
        self.assertEqual(ctx['day'], 1)  # якщо виписка в той самий день, фасад повертає 1

    @patch('hospital_admin.facades.CryptoFacade')
    def test_process_patient_discharge_financials_and_encryption(self, mock_crypto):
        """Перевірка математичних калькуляцій виписки та збереження в архів з шифруванням."""
        mock_crypto.encrypt.return_value = "archived_crypto_symptoms"

        dummy_context = {
            'name': 'Олексій', 'assignedDoctorName': 'Gregory', 'address': 'Львів',
            'mobile': '093111', 'symptoms': 'Застуда', 'admitDate': date.today(), 'day': 3
        }
        post_data = {'medicineCost': '200', 'roomCharge': '100', 'doctorFee': '300', 'OtherCharge': '50'}

        updated_ctx = AdminFacade.process_patient_discharge(patient_id=77, context=dummy_context, post_data=post_data)

        # Перевірка калькуляції: roomCharge = 100 * 3 дні = 300. total = 300 + 300 + 200 + 50 = 850
        self.assertEqual(updated_ctx['roomCharge'], 300)
        self.assertEqual(updated_ctx['total'], 850)

        # Перевірка, чи створився запис в архівній таблиці бд
        db_archive = PatientDischargeDetails.objects.get(patientId=77)
        self.assertEqual(db_archive.total, 850)
        self.assertEqual(db_archive.symptoms, "archived_crypto_symptoms")

    # =========================================================================
    # 5. ТЕСТИ ЗАПИСІВ НА ПРИЙОМ (Appointments)
    # =========================================================================

    def test_create_appointment_by_admin(self):
        """Перевірка автоматичного витягування імен з профілів User при призначенні прийому."""
        patient_user = User.objects.create_user(username='pat_user_test', first_name='Іван')

        app_mock_obj = Appointment()
        app_form = MagicMock()
        app_form.save.return_value = app_mock_obj

        # Передаємо id юзерів як doctor_id та patient_id відповідно до логіки методу
        new_app = AdminFacade.create_appointment_by_admin(app_form, doctor_id=self.doc_user.id,
                                                          patient_id=patient_user.id)

        self.assertEqual(new_app.doctorName, 'Gregory')
        self.assertEqual(new_app.patientName, 'Іван')
        self.assertTrue(new_app.status)