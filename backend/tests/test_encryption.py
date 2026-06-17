"""Tests para EncryptionService — TDD.

RED: Los tests fallan porque EncryptionService no existe.
GREEN: Se implementa y los tests pasan.
TRIANGULATE: string vacío, Unicode.
"""

import base64

import pytest

from app.core.config import Settings
from app.core.security import EncryptionService


class TestEncryptionRoundTrip:
    """Scenario: cifrar y descifrar recupera el valor original."""

    def test_encrypt_decrypt_round_trip(self) -> None:
        """WHEN encrypt y luego decrypt, THEN se recupera el original."""
        key = settings_encryption_key()
        svc = EncryptionService(key)
        original = "Hello, world!"

        ciphertext = svc.encrypt(original)
        decrypted = svc.decrypt(ciphertext)

        assert decrypted == original

    def test_encrypt_empty_string(self) -> None:
        """WHEN cifrar string vacío, THEN no falla y decrypt lo recupera."""
        key = settings_encryption_key()
        svc = EncryptionService(key)
        original = ""

        ciphertext = svc.encrypt(original)
        decrypted = svc.decrypt(ciphertext)

        assert decrypted == original

    def test_encrypt_unicode(self) -> None:
        """WHEN cifrar string con Unicode, THEN round-trip correcto."""
        key = settings_encryption_key()
        svc = EncryptionService(key)
        original = "José Pérez — ユーザー名"

        ciphertext = svc.encrypt(original)
        decrypted = svc.decrypt(ciphertext)

        assert decrypted == original


class TestEncryptionDeterminism:
    """Scenario: dos cifrados del mismo valor producen distintos outputs."""

    def test_two_encryptions_differ(self) -> None:
        """WHEN cifrar dos veces el mismo valor, THEN ciphertexts distintos."""
        key = settings_encryption_key()
        svc = EncryptionService(key)
        plaintext = "same value"

        c1 = svc.encrypt(plaintext)
        c2 = svc.encrypt(plaintext)

        assert c1 != c2


class TestEncryptionTamper:
    """Scenario: manipular ciphertext causa error."""

    def test_decrypt_tampered_ciphertext_raises(self) -> None:
        """WHEN decrypt con 1 byte alterado, THEN lanza excepción."""
        key = settings_encryption_key()
        svc = EncryptionService(key)
        ciphertext = svc.encrypt("secret data")

        # Decodificar, alterar un byte, recodificar
        raw = bytearray(base64.b64decode(ciphertext))
        raw[5] ^= 0xFF  # flip all bits in one byte
        tampered = base64.b64encode(bytes(raw)).decode()

        with pytest.raises(Exception):
            svc.decrypt(tampered)


class TestEncryptionKeyValidation:
    """Scenario: Settings valida longitud de ENCRYPTION_KEY."""

    def test_invalid_key_length_fails(self) -> None:
        """WHEN ENCRYPTION_KEY no tiene 32 bytes, THEN ValidationError."""
        with pytest.raises(Exception):
            Settings(encryption_key="too-short-key")

    def test_settings_uses_valid_key(self) -> None:
        """WHEN ENCRYPTION_KEY tiene 32 bytes, THEN Settings se instancia."""
        s = Settings(
            SECRET_KEY="a" * 32,
            ENCRYPTION_KEY="b" * 32,
            DATABASE_URL="postgresql+asyncpg://u:p@localhost/db",
        )
        assert s.encryption_key == "b" * 32


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def settings_encryption_key() -> bytes:
    """Retorna una encryption key de 32 bytes para tests."""
    return b"this-is-a-32-byte-test-key-!!!!!"
