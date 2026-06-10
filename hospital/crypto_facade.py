import os
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend


class CryptoFacade:
    _key = None

    @classmethod
    def _get_key(cls):
        """Отримує та готує 32-байтний ключ із .env для AES-256."""
        if cls._key is None:
            raw_key = os.environ.get('CRYPTO_KEY', 'fallback_secret_key_32_bytes_long!')
            # Гарантуємо рівно 32 байти (256 біт) за допомогою зрізу або доповнення нулями
            cls._key = raw_key.encode('utf-8')[:32].ljust(32, b'\0')
        return cls._key

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """Шифрує текст за алгоритмом AES-256-CBC."""
        if not plaintext:
            return plaintext
        try:
            key = cls._get_key()
            iv = os.urandom(16)  # Генеруємо випадковий вектор ініціалізації

            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()

            # Доповнення даних до розміру блоку (PKCS7)
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(plaintext.encode('utf-8')) + padder.finalize()

            ciphertext = encryptor.update(padded_data) + encryptor.finalize()

            # Повертаємо IV + зашифрований текст, закодовані в безпечний Base64 string
            return base64.b64encode(iv + ciphertext).decode('utf-8')
        except Exception as e:
            # Варіант А: виведе точну помилку в консоль терміналу, де запущено runserver
            print("\n!!! ПОМИЛКА ШИФРУВАННЯ !!!:", e, "\n")

            # Варіант Б: повністю зупинить сайт і покаже вам жовту сторінку Django з детальним Traceback
            raise e

    @classmethod
    def decrypt(cls, ciphertext_b64: str) -> str:
        """Дешифрує рядок Base64 назад у вихідний текст."""
        if not ciphertext_b64:
            return ciphertext_b64
        try:
            key = cls._get_key()
            raw_data = base64.b64decode(ciphertext_b64.encode('utf-8'))

            iv = raw_data[:16]  # Вилучаємо перші 16 байт (IV)
            ciphertext = raw_data[16:]  # Усе інше — зашифровані дані

            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()

            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

            # Знімаємо доповнення блоків PKCS7
            unpadder = padding.PKCS7(128).unpadder()
            plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

            return plaintext.decode('utf-8')
        except Exception:
            return ciphertext_b64