"""Tests para primitivas de seguridad — TDD estricto.

Cubre:
- 1.1 hash_password / verify_password (Argon2id)
- 1.2 encode_access_token / decode_token (PyJWT HS256)
- 1.3 email_lookup_hash (HMAC-SHA256)
- 1.4 generate_opaque_token / hash_token (opaco)
- 1.5 REFACTOR (extracción de constantes)
"""

import hashlib
import hmac

import pytest
from jwt import InvalidSignatureError, ExpiredSignatureError

from app.core.config import Settings
from app.core.security import (
    hash_password,
    verify_password,
    encode_access_token,
    decode_token,
    email_lookup_hash,
    generate_opaque_token,
    hash_token,
)


# ===========================================================================
# 1.1 hash_password / verify_password (Argon2id)
# ===========================================================================


class TestPasswordHashing:
    """Scenario: hash_password produce hash Argon2id y verify_password
    valida correctamente."""

    def test_hash_has_argon2id_prefix(self) -> None:
        """WHEN hash_password, THEN string comienza con $argon2id$."""
        hashed = hash_password("mi_password_segura")
        assert hashed.startswith("$argon2id$")

    def test_verify_correct_password(self) -> None:
        """WHEN verify_password con password correcta, THEN True."""
        hashed = hash_password("password_valida")
        assert verify_password("password_valida", hashed) is True

    def test_verify_incorrect_password(self) -> None:
        """WHEN verify_password con password incorrecta, THEN False."""
        hashed = hash_password("password_valida")
        assert verify_password("password_incorrecta", hashed) is False

    def test_hash_does_not_contain_plaintext(self) -> None:
        """WHEN hashear, THEN el hash NO contiene la password original."""
        password = "clave_super_secreta_123"
        hashed = hash_password(password)
        assert password not in hashed

    def test_different_passwords_produce_different_hashes(self) -> None:
        """WHEN hashear dos passwords distintas, THEN hashes distintos."""
        h1 = hash_password("pass1")
        h2 = hash_password("pass2")
        assert h1 != h2

    def test_same_password_produces_different_hashes(self) -> None:
        """WHEN hashear misma password dos veces, THEN hashes distintos
        (Argon2id usa salt aleatorio)."""
        h1 = hash_password("misma_pass")
        h2 = hash_password("misma_pass")
        assert h1 != h2

    def test_empty_password_raises(self) -> None:
        """WHEN hash_password con string vacío, THEN lanza ValueError."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            hash_password("")

    def test_verify_empty_hash_raises(self) -> None:
        """WHEN verify_password con hash vacío, THEN lanza ValueError."""
        with pytest.raises(ValueError):
            verify_password("pass", "")


# ===========================================================================
# 1.2 encode_access_token / decode_token (PyJWT HS256)
# ===========================================================================


class TestAccessToken:
    """Scenario: encode_access_token produce JWT firmado y decode_token
    lo valida."""

    def test_claims_minimos_presentes(self) -> None:
        """WHEN encode_access_token, THEN payload contiene todos los claims
        mínimos."""
        token = encode_access_token(
            sub="user-123",
            tenant_id="tenant-abc",
            roles=["admin", "tutor"],
        )
        payload = decode_token(token)
        assert payload["sub"] == "user-123"
        assert payload["tenant_id"] == "tenant-abc"
        assert payload["roles"] == ["admin", "tutor"]
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_expiration_is_15_minutes(self) -> None:
        """WHEN encode_access_token, THEN exp = iat + 15 minutos."""
        token = encode_access_token(
            sub="user-1",
            tenant_id="tenant-1",
            roles=["admin"],
        )
        payload = decode_token(token)
        exp_delta = payload["exp"] - payload["iat"]
        assert exp_delta == 15 * 60  # 15 minutos en segundos

    def test_tampered_signature_raises(self) -> None:
        """WHEN decode_token con payload alterado, THEN InvalidSignatureError."""
        token = encode_access_token(
            sub="user-1",
            tenant_id="tenant-1",
            roles=["admin"],
        )
        # Alterar un carácter en el payload (segunda parte del JWT),
        # manteniendo base64url válido
        parts = token.split(".")
        payload_b64 = list(parts[1])
        payload_b64[5] = "A" if payload_b64[5] != "A" else "B"
        parts[1] = "".join(payload_b64)
        tampered = ".".join(parts)
        with pytest.raises(InvalidSignatureError):
            decode_token(tampered)

    def test_expired_token_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """WHEN decode_token expirado, THEN ExpiredSignatureError."""
        # Setear expiración negativa para que el token expire inmediatamente
        monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "-1")
        token = encode_access_token(
            sub="user-1",
            tenant_id="tenant-1",
            roles=["admin"],
        )
        with pytest.raises(ExpiredSignatureError):
            decode_token(token)

    def test_wrong_token_type_raises(self) -> None:
        """WHEN decode_token con type != 'access', THEN ValueError."""
        import jwt as pyjwt
        from datetime import datetime, timedelta, timezone

        settings = Settings()
        now = datetime.now(timezone.utc)
        payload = {
            "sub": "user-1",
            "tenant_id": "tenant-1",
            "roles": ["admin"],
            "type": "refresh",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
        }
        token = pyjwt.encode(payload, settings.secret_key, algorithm="HS256")
        with pytest.raises(ValueError, match="Token type must be 'access'"):
            decode_token(token)

    def test_invalid_token_raises(self) -> None:
        """WHEN decode_token con string basura, THEN error."""
        with pytest.raises(Exception):
            decode_token("esto-no-es-un-token")


# ===========================================================================
# 1.3 email_lookup_hash (HMAC-SHA256)
# ===========================================================================


class TestEmailLookupHash:
    """Scenario: email_lookup_hash produce hash determinístico y consistente."""

    def test_mismo_email_mismo_hash(self) -> None:
        """WHEN mismo email dos veces, THEN mismo hash."""
        h1 = email_lookup_hash("usuario@example.com")
        h2 = email_lookup_hash("usuario@example.com")
        assert h1 == h2

    def test_emails_distintos_hashes_distintos(self) -> None:
        """WHEN emails distintos, THEN hashes distintos."""
        h1 = email_lookup_hash("a@example.com")
        h2 = email_lookup_hash("b@example.com")
        assert h1 != h2

    def test_normalizacion_trim_y_lowercase(self) -> None:
        """WHEN email con espacios y mayúsculas, THEN hash = mismo que lowercase
        sin espacios."""
        h1 = email_lookup_hash("  Usuario@Example.Com  ")
        h2 = email_lookup_hash("usuario@example.com")
        assert h1 == h2

    def test_no_contiene_email_original(self) -> None:
        """WHEN hashear, THEN resultado no contiene el email original."""
        email = "secreto@example.com"
        h = email_lookup_hash(email)
        assert email not in h

    def test_deterministico_misma_key(self) -> None:
        """WHEN mismo email mismo settings, THEN siempre mismo hash."""
        resultados = {email_lookup_hash("test@test.com") for _ in range(5)}
        assert len(resultados) == 1

    def test_formato_hex(self) -> None:
        """WHEN hashear, THEN resultado es string hexadecimal."""
        h = email_lookup_hash("a@b.com")
        # Verificar que es un hex string válido (64 chars para SHA-256)
        assert len(h) == 64
        int(h, 16)  # No lanza ValueError


# ===========================================================================
# 1.4 generate_opaque_token / hash_token
# ===========================================================================


class TestOpaqueToken:
    """Scenario: generate_opaque_token produce token de alta entropía
    y hash_token produce hash determinístico."""

    def test_token_tiene_alta_entropia(self) -> None:
        """WHEN generate_opaque_token, THEN token tiene al menos 32 bytes de
        entropía (43+ chars en base64url)."""
        token = generate_opaque_token()
        # 32 bytes → 43 caracteres en base64url (sin padding)
        assert len(token) >= 43

    def test_hash_deterministico(self) -> None:
        """WHEN hash_token con mismo token, THEN mismo hash."""
        token = generate_opaque_token()
        h1 = hash_token(token)
        h2 = hash_token(token)
        assert h1 == h2

    def test_token_en_claro_no_es_hash(self) -> None:
        """WHEN hash_token, THEN resultado ≠ token original."""
        token = generate_opaque_token()
        h = hash_token(token)
        assert token != h

    def test_tokens_distintos_producen_hashes_distintos(self) -> None:
        """WHEN hash_token con tokens distintos, THEN hashes distintos."""
        t1 = generate_opaque_token()
        t2 = generate_opaque_token()
        assert hash_token(t1) != hash_token(t2)

    def test_dos_llamadas_producen_tokens_distintos(self) -> None:
        """WHEN generate_opaque_token dos veces, THEN tokens distintos."""
        t1 = generate_opaque_token()
        t2 = generate_opaque_token()
        assert t1 != t2

    def test_hash_formato_hex(self) -> None:
        """WHEN hash_token, THEN resultado es hex string."""
        token = generate_opaque_token()
        h = hash_token(token)
        assert len(h) == 64  # SHA-256 → 64 hex chars
        int(h, 16)  # Es hex válido
