"""EncryptionService: cifrado AES-256-GCM para PII y secretos en reposo.

Uso::

    from app.core.security import encryption_service
    ct = encryption_service.encrypt("CBU: 123...")
    pt = encryption_service.decrypt(ct)
"""

import base64
import os
from functools import lru_cache

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import Settings


class EncryptionService:
    """Cifrado AES-256-GCM con IV de 12 bytes aleatorios.

    Serializa el ciphertext como ``base64(iv + ciphertext)``.
    """

    def __init__(self, key: bytes) -> None:
        if len(key) != 32:
            msg = f"AES-256 requiere key de 32 bytes, se recibieron {len(key)}"
            raise ValueError(msg)
        self._aesgcm = AESGCM(key)

    def encrypt(self, plaintext: str) -> str:
        """Cifra un string y retorna base64(iv + ciphertext)."""
        iv = os.urandom(12)
        ct = self._aesgcm.encrypt(iv, plaintext.encode("utf-8"), None)
        return base64.b64encode(iv + ct).decode("ascii")

    def decrypt(self, ciphertext_b64: str) -> str:
        """Descifra un base64(iv + ciphertext) y retorna el string original."""
        raw = base64.b64decode(ciphertext_b64)
        iv, ct = raw[:12], raw[12:]
        return self._aesgcm.decrypt(iv, ct, None).decode("utf-8")


@lru_cache
def get_encryption_service() -> EncryptionService:
    """Retorna el singleton de EncryptionService (cacheado por Settings)."""
    settings = Settings()
    return EncryptionService(settings.encryption_key.encode())


# Singleton módulo-level para uso directo
encryption_service = EncryptionService(
    Settings().encryption_key.encode(),
)
