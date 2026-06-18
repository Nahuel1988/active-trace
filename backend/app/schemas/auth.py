"""Pydantic v2 schemas for authentication requests and responses.

All schemas use `extra='forbid'` as per project convention to reject
unknown fields at the API boundary.
"""

import re

from pydantic import BaseModel, ConfigDict, field_validator

# ── Shared validation helpers ─────────────────────────────────────────────


def _validate_email(value: str) -> str:
    """Validate email has a basic valid format.

    Strips leading/trailing whitespace before checking.
    Uses a regex that requires local-part@domain.tld structure.
    """
    stripped = value.strip()
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', stripped):
        raise ValueError('Formato de email inválido')
    return stripped


def _validate_password(value: str) -> str:
    """Validate password meets minimum length requirement (8 chars)."""
    if len(value) < 8:
        raise ValueError('La contraseña debe tener al menos 8 caracteres')
    return value


def _validate_totp_code(value: str) -> str:
    """Validate a TOTP code is exactly 6 digits."""
    if not re.match(r'^\d{6}$', value):
        raise ValueError('El código debe tener exactamente 6 dígitos')
    return value


# ── Request Schemas ───────────────────────────────────────────────────────


class LoginRequest(BaseModel):
    """Request body for POST /api/auth/login.

    Validates email format and password minimum length.
    """
    model_config = ConfigDict(extra='forbid')

    email: str
    password: str

    _validate_email = field_validator('email')(_validate_email)
    _validate_password = field_validator('password')(_validate_password)


class RefreshRequest(BaseModel):
    """Request body for POST /api/auth/refresh."""
    model_config = ConfigDict(extra='forbid')

    refresh_token: str


class LogoutRequest(BaseModel):
    """Request body for POST /api/auth/logout."""
    model_config = ConfigDict(extra='forbid')

    refresh_token: str


class TwoFAConfirmRequest(BaseModel):
    """Request body for POST /api/auth/2fa/confirm.

    Validates the TOTP code during 2FA enrollment confirmation.
    """
    model_config = ConfigDict(extra='forbid')

    code: str

    _validate_code = field_validator('code')(_validate_totp_code)


class TwoFAVerifyRequest(BaseModel):
    """Request body for POST /api/auth/2fa/verify.

    Validates the 2FA challenge JWT + TOTP code during login with 2FA.
    """
    model_config = ConfigDict(extra='forbid')

    challenge: str
    code: str

    _validate_code = field_validator('code')(_validate_totp_code)


class ForgotRequest(BaseModel):
    """Request body for POST /api/auth/forgot.

    Validates email format before sending reset link.
    """
    model_config = ConfigDict(extra='forbid')

    email: str

    _validate_email = field_validator('email')(_validate_email)


class ResetRequest(BaseModel):
    """Request body for POST /api/auth/reset.

    Validates new password minimum length.
    """
    model_config = ConfigDict(extra='forbid')

    token: str
    new_password: str

    _validate_new_password = field_validator('new_password')(_validate_password)


# ── Response Schemas ──────────────────────────────────────────────────────


class TokenPair(BaseModel):
    """Response containing access + refresh token pair.

    Returned after successful login (or 2FA verify if enabled).
    """
    model_config = ConfigDict(extra='forbid')

    access_token: str
    refresh_token: str
    token_type: str = 'bearer'


class TwoFAEnrollResponse(BaseModel):
    """Response after enrolling in 2FA (before confirmation).

    Contains the OTP auth URI for QR code generation and the
    plain-text secret for manual entry.
    """
    model_config = ConfigDict(extra='forbid')

    otpauth_uri: str
    secret: str


class TwoFAChallenge(BaseModel):
    """Response when 2FA is required after password validation.

    The client must present this challenge JWT together with
    a valid TOTP code to POST /api/auth/2fa/verify to complete login.
    """
    model_config = ConfigDict(extra='forbid')

    challenge: str
    type: str = '2fa_challenge'


class MessageResponse(BaseModel):
    """Generic message response for informational endpoints."""
    model_config = ConfigDict(extra='forbid')

    message: str


class CurrentUserResponse(BaseModel):
    """Response for the current authenticated user's identity.

    Returned by the get_current_user dependency and
    GET /api/auth/me endpoint.
    """
    model_config = ConfigDict(extra='forbid')

    user_id: str
    tenant_id: str
    roles: list[str]
