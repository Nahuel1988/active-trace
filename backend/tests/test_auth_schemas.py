"""Tests para schemas Pydantic de auth — TDD estricto.

Cubre:
- 4.1.1 LoginRequest: validación y extra='forbid'
- 4.1.2 RefreshRequest / LogoutRequest: validación básica
- 4.1.3 TwoFAConfirmRequest / TwoFAVerifyRequest: validación de código TOTP
- 4.1.4 ForgotRequest / ResetRequest: validación de email y password
- 4.1.5 TokenPair: serialización
- 4.1.6 Response schemas: no exponen PII ni hashes
- 4.1.7 Todos los schemas: validación y serialización
"""

import pytest
from pydantic import ValidationError

from app.schemas.auth import (
    CurrentUserResponse,
    ForgotRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    ResetRequest,
    TokenPair,
    TwoFAChallenge,
    TwoFAConfirmRequest,
    TwoFAEnrollResponse,
    TwoFAVerifyRequest,
)


# ===========================================================================
# 4.1.1 LoginRequest
# ===========================================================================


class TestLoginRequest:
    """Scenario: LoginRequest valida email y password correctamente."""

    def test_valid_login(self) -> None:
        """WHEN email y password válidos, THEN crea instancia."""
        data = LoginRequest(email="user@example.com", password="12345678")
        assert data.email == "user@example.com"
        assert data.password == "12345678"

    def test_extra_field_rejected(self) -> None:
        """WHEN campo extra, THEN ValidationError (extra='forbid')."""
        with pytest.raises(ValidationError):
            LoginRequest(email="user@example.com", password="12345678", extra="should-fail")  # type: ignore[call-arg]

    def test_invalid_email_format(self) -> None:
        """WHEN email sin @, THEN ValidationError."""
        with pytest.raises(ValidationError):
            LoginRequest(email="not-an-email", password="12345678")

    def test_email_without_domain(self) -> None:
        """WHEN email incompleto, THEN ValidationError."""
        with pytest.raises(ValidationError):
            LoginRequest(email="user@", password="12345678")

    def test_email_without_at(self) -> None:
        """WHEN email sin dominio, THEN ValidationError."""
        with pytest.raises(ValidationError):
            LoginRequest(email="user.at.example.com", password="12345678")

    def test_empty_email(self) -> None:
        """WHEN email vacío, THEN ValidationError."""
        with pytest.raises(ValidationError):
            LoginRequest(email="", password="12345678")

    def test_password_too_short(self) -> None:
        """WHEN password < 8 chars, THEN ValidationError."""
        with pytest.raises(ValidationError):
            LoginRequest(email="user@example.com", password="1234567")

    def test_password_exactly_8_chars(self) -> None:
        """WHEN password = 8 chars, THEN OK (boundary)."""
        data = LoginRequest(email="user@example.com", password="12345678")
        assert data.password == "12345678"

    def test_empty_password(self) -> None:
        """WHEN password vacía, THEN ValidationError."""
        with pytest.raises(ValidationError):
            LoginRequest(email="user@example.com", password="")

    def test_serialize_to_dict(self) -> None:
        """WHEN model_dump(), THEN dict con todos los campos."""
        data = LoginRequest(email="a@b.com", password="12345678")
        assert data.model_dump() == {"email": "a@b.com", "password": "12345678"}


# ===========================================================================
# 4.1.2 RefreshRequest / LogoutRequest
# ===========================================================================


class TestRefreshRequest:
    """Scenario: RefreshRequest valida refresh_token."""

    def test_valid_refresh(self) -> None:
        """WHEN refresh_token presente, THEN crea instancia."""
        data = RefreshRequest(refresh_token="some-token")
        assert data.refresh_token == "some-token"

    def test_extra_field_rejected(self) -> None:
        """WHEN campo extra, THEN ValidationError."""
        with pytest.raises(ValidationError):
            RefreshRequest(refresh_token="token", extra="x")  # type: ignore[call-arg]

    def test_empty_token(self) -> None:
        """WHEN refresh_token vacío, THEN crea (string vacío es válido como str)."""
        data = RefreshRequest(refresh_token="")
        assert data.refresh_token == ""

    def test_serialize(self) -> None:
        """WHEN model_dump(), THEN dict."""
        data = RefreshRequest(refresh_token="abc")
        assert data.model_dump() == {"refresh_token": "abc"}


class TestLogoutRequest:
    """Scenario: LogoutRequest valida refresh_token."""

    def test_valid_logout(self) -> None:
        """WHEN refresh_token presente, THEN crea instancia."""
        data = LogoutRequest(refresh_token="some-token")
        assert data.refresh_token == "some-token"

    def test_extra_field_rejected(self) -> None:
        """WHEN campo extra, THEN ValidationError."""
        with pytest.raises(ValidationError):
            LogoutRequest(refresh_token="token", extra="x")  # type: ignore[call-arg]

    def test_serialize(self) -> None:
        """WHEN model_dump(), THEN dict."""
        data = LogoutRequest(refresh_token="abc")
        assert data.model_dump() == {"refresh_token": "abc"}


# ===========================================================================
# 4.1.3 TwoFAConfirmRequest / TwoFAVerifyRequest
# ===========================================================================


class TestTwoFAConfirmRequest:
    """Scenario: TwoFAConfirmRequest valida código TOTP de 6 dígitos."""

    def test_valid_code(self) -> None:
        """WHEN código de 6 dígitos, THEN crea instancia."""
        data = TwoFAConfirmRequest(code="123456")
        assert data.code == "123456"

    def test_extra_field_rejected(self) -> None:
        """WHEN campo extra, THEN ValidationError."""
        with pytest.raises(ValidationError):
            TwoFAConfirmRequest(code="123456", extra="x")  # type: ignore[call-arg]

    def test_code_less_than_6_digits(self) -> None:
        """WHEN código < 6 dígitos, THEN ValidationError."""
        with pytest.raises(ValidationError):
            TwoFAConfirmRequest(code="12345")

    def test_code_more_than_6_digits(self) -> None:
        """WHEN código > 6 dígitos, THEN ValidationError."""
        with pytest.raises(ValidationError):
            TwoFAConfirmRequest(code="1234567")

    def test_code_with_letters(self) -> None:
        """WHEN código con letras, THEN ValidationError."""
        with pytest.raises(ValidationError):
            TwoFAConfirmRequest(code="abc123")

    def test_code_empty_string(self) -> None:
        """WHEN código vacío, THEN ValidationError."""
        with pytest.raises(ValidationError):
            TwoFAConfirmRequest(code="")

    def test_serialize(self) -> None:
        """WHEN model_dump(), THEN dict."""
        data = TwoFAConfirmRequest(code="000000")
        assert data.model_dump() == {"code": "000000"}


class TestTwoFAVerifyRequest:
    """Scenario: TwoFAVerifyRequest valida challenge + código TOTP."""

    def test_valid_verify(self) -> None:
        """WHEN challenge y código válidos, THEN crea instancia."""
        data = TwoFAVerifyRequest(challenge="jwt-challenge", code="654321")
        assert data.challenge == "jwt-challenge"
        assert data.code == "654321"

    def test_extra_field_rejected(self) -> None:
        """WHEN campo extra, THEN ValidationError."""
        with pytest.raises(ValidationError):
            TwoFAVerifyRequest(challenge="c", code="123456", extra="x")  # type: ignore[call-arg]

    def test_invalid_code_format(self) -> None:
        """WHEN código inválido, THEN ValidationError."""
        with pytest.raises(ValidationError):
            TwoFAVerifyRequest(challenge="c", code="12a456")

    def test_empty_challenge(self) -> None:
        """WHEN challenge vacío, THEN crea (str vacío válido)."""
        data = TwoFAVerifyRequest(challenge="", code="123456")
        assert data.challenge == ""

    def test_serialize(self) -> None:
        """WHEN model_dump(), THEN dict."""
        data = TwoFAVerifyRequest(challenge="abc", code="999999")
        assert data.model_dump() == {"challenge": "abc", "code": "999999"}


# ===========================================================================
# 4.1.4 ForgotRequest / ResetRequest
# ===========================================================================


class TestForgotRequest:
    """Scenario: ForgotRequest valida email."""

    def test_valid_email(self) -> None:
        """WHEN email válido, THEN crea instancia."""
        data = ForgotRequest(email="user@example.com")
        assert data.email == "user@example.com"

    def test_extra_field_rejected(self) -> None:
        """WHEN campo extra, THEN ValidationError."""
        with pytest.raises(ValidationError):
            ForgotRequest(email="user@example.com", extra="x")  # type: ignore[call-arg]

    def test_invalid_email_format(self) -> None:
        """WHEN email inválido, THEN ValidationError."""
        with pytest.raises(ValidationError):
            ForgotRequest(email="not-an-email")

    def test_empty_email(self) -> None:
        """WHEN email vacío, THEN ValidationError."""
        with pytest.raises(ValidationError):
            ForgotRequest(email="")

    def test_serialize(self) -> None:
        """WHEN model_dump(), THEN dict."""
        data = ForgotRequest(email="a@b.com")
        assert data.model_dump() == {"email": "a@b.com"}


class TestResetRequest:
    """Scenario: ResetRequest valida token y new_password."""

    def test_valid_reset(self) -> None:
        """WHEN token y password válidos, THEN crea instancia."""
        data = ResetRequest(token="reset-token", new_password="newpass123")
        assert data.token == "reset-token"
        assert data.new_password == "newpass123"

    def test_extra_field_rejected(self) -> None:
        """WHEN campo extra, THEN ValidationError."""
        with pytest.raises(ValidationError):
            ResetRequest(token="t", new_password="12345678", extra="x")  # type: ignore[call-arg]

    def test_new_password_too_short(self) -> None:
        """WHEN new_password < 8 chars, THEN ValidationError."""
        with pytest.raises(ValidationError):
            ResetRequest(token="t", new_password="1234567")

    def test_new_password_exactly_8_chars(self) -> None:
        """WHEN new_password = 8 chars, THEN OK (boundary)."""
        data = ResetRequest(token="t", new_password="12345678")
        assert data.new_password == "12345678"

    def test_empty_new_password(self) -> None:
        """WHEN new_password vacía, THEN ValidationError."""
        with pytest.raises(ValidationError):
            ResetRequest(token="t", new_password="")

    def test_empty_token(self) -> None:
        """WHEN token vacío, THEN crea (str vacío válido)."""
        data = ResetRequest(token="", new_password="12345678")
        assert data.token == ""

    def test_serialize(self) -> None:
        """WHEN model_dump(), THEN dict."""
        data = ResetRequest(token="t", new_password="12345678")
        assert data.model_dump() == {"token": "t", "new_password": "12345678"}


# ===========================================================================
# 4.1.5 TokenPair
# ===========================================================================


class TestTokenPair:
    """Scenario: TokenPair serializa access+refresh tokens."""

    def test_create_with_all_fields(self) -> None:
        """WHEN todos los campos, THEN crea instancia."""
        data = TokenPair(access_token="access-123", refresh_token="refresh-456")
        assert data.access_token == "access-123"
        assert data.refresh_token == "refresh-456"
        assert data.token_type == "bearer"

    def test_default_token_type_is_bearer(self) -> None:
        """WHEN sin token_type, THEN default 'bearer'."""
        data = TokenPair(access_token="a", refresh_token="b")
        assert data.token_type == "bearer"

    def test_custom_token_type(self) -> None:
        """WHEN token_type explícito, THEN usa el valor dado."""
        data = TokenPair(access_token="a", refresh_token="b", token_type="Bearer")
        assert data.token_type == "Bearer"

    def test_extra_field_rejected(self) -> None:
        """WHEN campo extra, THEN ValidationError."""
        with pytest.raises(ValidationError):
            TokenPair(access_token="a", refresh_token="b", extra="x")  # type: ignore[call-arg]

    def test_serialize_includes_defaults(self) -> None:
        """WHEN model_dump(), THEN incluye token_type con default."""
        data = TokenPair(access_token="at", refresh_token="rt")
        assert data.model_dump() == {
            "access_token": "at",
            "refresh_token": "rt",
            "token_type": "bearer",
        }

    def test_serialize_with_custom_type(self) -> None:
        """WHEN model_dump() con custom token_type, THEN lo respeta."""
        data = TokenPair(access_token="at", refresh_token="rt", token_type="dpop")
        assert data.model_dump()["token_type"] == "dpop"

    def test_serialize_no_pii(self) -> None:
        """WHEN model_dump(), THEN no contiene password ni hash."""
        data = TokenPair(access_token="at", refresh_token="rt")
        dumped = data.model_dump()
        sensitive_keys = {"password", "password_hash", "hash", "email", "secret"}
        assert sensitive_keys.isdisjoint(dumped.keys())


# ===========================================================================
# 4.1.6 Response schemas — no exponen PII ni hashes
# ===========================================================================


class TestResponseSchemasNoPII:
    """Scenario: Ningún response schema expone password, hash, email, etc."""

    # Conjunto de palabras que indican datos sensibles en nombres de campo
    _SENSITIVE_SUBSTRINGS = {"password", "hash", "token_hash", "email_encrypted"}

    @staticmethod
    def _field_names(model_class: type) -> set[str]:
        return set(model_class.model_fields.keys())

    def test_token_pair_no_sensitive_fields(self) -> None:
        """WHEN TokenPair fields, THEN ningún campo es sensible."""
        fields = self._field_names(TokenPair)
        sensitive = {f for f in fields if any(s in f.lower() for s in self._SENSITIVE_SUBSTRINGS)}
        assert not sensitive, f"Campos sensibles encontrados en TokenPair: {sensitive}"

    def test_two_fa_enroll_no_sensitive_fields(self) -> None:
        """WHEN TwoFAEnrollResponse fields, THEN ningún campo interno sensible."""
        fields = self._field_names(TwoFAEnrollResponse)
        sensitive = {f for f in fields if any(s in f.lower() for s in self._SENSITIVE_SUBSTRINGS)}
        assert not sensitive, f"Campos sensibles encontrados en TwoFAEnrollResponse: {sensitive}"

    def test_two_fa_challenge_no_sensitive_fields(self) -> None:
        """WHEN TwoFAChallenge fields, THEN ningún campo sensible."""
        fields = self._field_names(TwoFAChallenge)
        sensitive = {f for f in fields if any(s in f.lower() for s in self._SENSITIVE_SUBSTRINGS)}
        assert not sensitive, f"Campos sensibles encontrados en TwoFAChallenge: {sensitive}"

    def test_message_response_no_sensitive_fields(self) -> None:
        """WHEN MessageResponse fields, THEN ningún campo sensible."""
        fields = self._field_names(MessageResponse)
        sensitive = {f for f in fields if any(s in f.lower() for s in self._SENSITIVE_SUBSTRINGS)}
        assert not sensitive, f"Campos sensibles encontrados en MessageResponse: {sensitive}"

    def test_current_user_no_sensitive_fields(self) -> None:
        """WHEN CurrentUserResponse fields, THEN ningún campo sensible."""
        fields = self._field_names(CurrentUserResponse)
        sensitive = {f for f in fields if any(s in f.lower() for s in self._SENSITIVE_SUBSTRINGS)}
        assert not sensitive, f"Campos sensibles encontrados en CurrentUserResponse: {sensitive}"


# ===========================================================================
# 4.1.7 Todos los response schemas serializan correctamente
# ===========================================================================


class TestResponseSchemasSerialization:
    """Scenario: Todos los response schemas serializan correctamente."""

    def test_token_pair_serialization(self) -> None:
        """WHEN TokenPair creado, THEN model_dump() con todos los campos."""
        data = TokenPair(access_token="a", refresh_token="r")
        dumped = data.model_dump()
        assert dumped["access_token"] == "a"
        assert dumped["refresh_token"] == "r"
        assert dumped["token_type"] == "bearer"

    def test_two_fa_enroll_serialization(self) -> None:
        """WHEN TwoFAEnrollResponse creado, THEN model_dump() correcto."""
        data = TwoFAEnrollResponse(otpauth_uri="otpauth://...", secret="JBSWY3DPEHPK3PXP")
        dumped = data.model_dump()
        assert dumped["otpauth_uri"] == "otpauth://..."
        assert dumped["secret"] == "JBSWY3DPEHPK3PXP"

    def test_two_fa_challenge_default_type(self) -> None:
        """WHEN TwoFAChallenge sin type, THEN default '2fa_challenge'."""
        data = TwoFAChallenge(challenge="jwt-challenge")
        dumped = data.model_dump()
        assert dumped["challenge"] == "jwt-challenge"
        assert dumped["type"] == "2fa_challenge"

    def test_two_fa_challenge_custom_type(self) -> None:
        """WHEN TwoFAChallenge con type custom, THEN lo respeta."""
        data = TwoFAChallenge(challenge="c", type="custom")
        assert data.model_dump()["type"] == "custom"

    def test_message_response_serialization(self) -> None:
        """WHEN MessageResponse creado, THEN model_dump() correcto."""
        data = MessageResponse(message="Operación exitosa")
        assert data.model_dump() == {"message": "Operación exitosa"}

    def test_current_user_response_serialization(self) -> None:
        """WHEN CurrentUserResponse creado, THEN model_dump() correcto."""
        data = CurrentUserResponse(
            user_id="uuid-user",
            tenant_id="uuid-tenant",
            roles=["admin", "tutor"],
        )
        dumped = data.model_dump()
        assert dumped["user_id"] == "uuid-user"
        assert dumped["tenant_id"] == "uuid-tenant"
        assert dumped["roles"] == ["admin", "tutor"]

    def test_current_user_response_empty_roles(self) -> None:
        """WHEN CurrentUserResponse sin roles, THEN lista vacía."""
        data = CurrentUserResponse(user_id="u", tenant_id="t", roles=[])
        assert data.model_dump()["roles"] == []


# ===========================================================================
# 4.1.8 Todos los request schemas validan entrada (extra='forbid')
# ===========================================================================


class TestAllRequestSchemasForbidExtra:
    """Scenario: Todos los request schemas rechazan campos extra."""

    @pytest.mark.parametrize(
        "schema_class,valid_kwargs",
        [
            (LoginRequest, {"email": "a@b.com", "password": "12345678"}),
            (RefreshRequest, {"refresh_token": "tok"}),
            (LogoutRequest, {"refresh_token": "tok"}),
            (TwoFAConfirmRequest, {"code": "123456"}),
            (TwoFAVerifyRequest, {"challenge": "c", "code": "123456"}),
            (ForgotRequest, {"email": "a@b.com"}),
            (ResetRequest, {"token": "t", "new_password": "12345678"}),
        ],
    )
    def test_extra_field_rejected(self, schema_class: type, valid_kwargs: dict) -> None:
        """WHEN campo extra agregado, THEN ValidationError."""
        kwargs = {**valid_kwargs, "extra_field": "should-fail"}
        with pytest.raises(ValidationError):
            schema_class(**kwargs)  # type: ignore[call-arg]

    @pytest.mark.parametrize(
        "schema_class,valid_kwargs",
        [
            (LoginRequest, {"email": "a@b.com", "password": "12345678"}),
            (RefreshRequest, {"refresh_token": "tok"}),
            (LogoutRequest, {"refresh_token": "tok"}),
            (TwoFAConfirmRequest, {"code": "123456"}),
            (TwoFAVerifyRequest, {"challenge": "c", "code": "123456"}),
            (ForgotRequest, {"email": "a@b.com"}),
            (ResetRequest, {"token": "t", "new_password": "12345678"}),
        ],
    )
    def test_valid_creation(self, schema_class: type, valid_kwargs: dict) -> None:
        """WHEN kwargs válidos, THEN crea instancia sin errores."""
        instance = schema_class(**valid_kwargs)
        assert instance is not None
