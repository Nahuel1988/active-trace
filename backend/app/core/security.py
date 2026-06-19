"""EncryptionService: cifrado AES-256-GCM para PII y secretos en reposo.
Primitivas de seguridad: Argon2id para passwords, JWT HS256 para tokens,
HMAC-SHA256 para email lookup, generación de tokens opacos.

Uso::

    from app.core.security import encryption_service
    ct = encryption_service.encrypt("CBU: 123...")
    pt = encryption_service.decrypt(ct)

    from app.core.security import hash_password, verify_password
    h = hash_password("mi_password")
    assert verify_password("mi_password", h)
"""

import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from functools import lru_cache

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import Settings

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
DEFAULT_ACCESS_EXPIRE_MINUTES = 15
DEFAULT_OPAQUE_TOKEN_BYTES = 32

# ---------------------------------------------------------------------------
# Argon2id — PasswordHasher singleton
# ---------------------------------------------------------------------------
_ph = PasswordHasher()


def hash_password(password: str) -> str:
    """Genera hash Argon2id de la password.

    Raises:
        ValueError: si la password está vacía.
    """
    if not password:
        msg = "Password cannot be empty"
        raise ValueError(msg)
    return _ph.hash(password)


def verify_password(password: str, hash_value: str) -> bool:
    """Verifica password contra hash Argon2id.

    Returns:
        True si coincide, False en cualquier otro caso.
    """
    if not hash_value:
        msg = "Hash cannot be empty"
        raise ValueError(msg)
    try:
        return _ph.verify(hash_value, password)
    except VerifyMismatchError:
        return False


# ---------------------------------------------------------------------------
# JWT HS256 — encode / decode
# ---------------------------------------------------------------------------


def encode_access_token(
    sub: str,
    tenant_id: str,
    roles: list[str],
    *,
    impersonated: bool = False,
    actor_id: str | None = None,
) -> str:
    """Emite un JWT access token firmado con HS256.

    Claims mínimos: sub, tenant_id, roles, exp, iat, type='access'.

    En sesiones de impersonación incluye además ``impersonated=true``
    y ``actor_id`` (UUID del usuario real que impersona).

    Args:
        sub: UUID del usuario (string).
        tenant_id: UUID del tenant (string).
        roles: Lista de códigos de rol.
        impersonated: ``True`` si es un token de impersonación.
        actor_id: UUID del actor real (string). Si es ``None``
            en impersonación, se usa ``sub``.
    """
    settings = Settings()
    now = datetime.now(timezone.utc)
    payload: dict = {
        "sub": sub,
        "tenant_id": tenant_id,
        "roles": roles,
        "type": "access",
        "impersonated": impersonated,
        "iat": int(now.timestamp()),
        "exp": int(
            (now + timedelta(minutes=settings.access_token_expire_minutes)).timestamp()
        ),
    }
    # En sesión normal, actor_id = sub (misma identidad)
    if impersonated:
        payload["actor_id"] = actor_id or sub
    else:
        payload["actor_id"] = sub
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_token(token: str) -> dict:
    """Decodifica y verifica un JWT access token.

    Raises:
        jwt.InvalidSignatureError: firma inválida.
        jwt.ExpiredSignatureError: token vencido.
        ValueError: type != 'access'.
    """
    settings = Settings()
    payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    if payload.get("type") != "access":
        msg = f"Token type must be 'access', got '{payload.get('type')}'"
        raise ValueError(msg)
    return payload


# ---------------------------------------------------------------------------
# Email lookup hash — HMAC-SHA256 determinístico
# ---------------------------------------------------------------------------


def email_lookup_hash(email: str) -> str:
    """Hash determinístico del email para búsqueda por login.

    Normaliza: trim + lowercase antes de hashear.
    """
    settings = Settings()
    normalized = email.strip().lower()
    return hmac.new(
        settings.email_lookup_hmac_key.encode(),
        normalized.encode(),
        hashlib.sha256,
    ).hexdigest()


# ---------------------------------------------------------------------------
# Tokens opacos — refresh, password reset
# ---------------------------------------------------------------------------


def generate_opaque_token() -> str:
    """Genera un token opaco de alta entropía (32 bytes, base64url)."""
    return secrets.token_urlsafe(DEFAULT_OPAQUE_TOKEN_BYTES)


def hash_token(token: str) -> str:
    """Hash SHA-256 del token opaco para persistencia en DB."""
    return hashlib.sha256(token.encode()).hexdigest()


# ===========================================================================
# EncryptionService (no modificar)
# ===========================================================================

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
