from django.test import TestCase
from hospital_admin.facades import CryptoFacade


class CryptoFacadeTest(TestCase):
    """Тестування інфраструктурного крипто-фасаду (AES-256-CBC)."""

    def setUp(self):
        self.plain_text = "Пацієнт скаржиться на гострий головний біль та мігрень."

    def test_encryption_and_decryption_cycle(self):
        """Перевірка повного циклу: заміна тексту на шифротекст і повне відновлення."""
        ciphertext = CryptoFacade.encrypt(self.plain_text)

        self.assertIsNotNone(ciphertext)
        self.assertNotEqual(self.plain_text, ciphertext)

        # Перевірка зворотного перетворення
        decrypted = CryptoFacade.decrypt(ciphertext)
        self.assertEqual(self.plain_text, decrypted)

    def test_dynamic_iv_uniqueness(self):
        """Перевірка, що однаковий текст щоразу дає унікальний шифротекст (захист від статистичного аналізу)."""
        cipher_1 = CryptoFacade.encrypt(self.plain_text)
        cipher_2 = CryptoFacade.encrypt(self.plain_text)

        self.assertNotEqual(cipher_1, cipher_2)

    def test_empty_string_handling(self):
        """Перевірка стійкості фасаду при спробі зашифрувати порожній рядок."""
        empty_cipher = CryptoFacade.encrypt("")
        self.assertIsNotNone(empty_cipher)
        self.assertEqual(CryptoFacade.decrypt(empty_cipher), "")