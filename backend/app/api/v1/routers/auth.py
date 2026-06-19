"""Auth router — 2FA endpoints (enroll, confirm, verify).

This router is part of the authentication module and handles all
TOTP/2FA-related operations:

- ``POST /api/auth/2fa/enroll``   — generate + persist TOTP secret
- ``POST /api/auth/2fa/confirm``  — confirm enrollment with a code
- ``POST /api/auth/2fa/verify``   — verify challenge + code → token pair

Business logic lives in ``TotpService``; routers only wire dependencies.
"""

import logging
from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.dependencies import (
    CurrentUser,
    get_current_user,
    get_db,
    get_settings,
    get_token_service,
    get_totp_service,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    MessageResponse,
    TwoFAConfirmRequest,
    TwoFAEnrollResponse,
    TwoFAVerifyRequest,
    TokenPair,
)
from app.services.token_service import TokenService
from app.services.totp_service import TotpService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth/2fa", tags=["auth"])


async def get_current_user_from_challenge(  # noqa: RUF029
    body: TwoFAVerifyRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    """Extract the user from a 2FA challenge JWT (used in the verify endpoint).

    The challenge token is a short-lived JWT issued after password
    validation.  This dependency decodes it and returns the ``User``
    object so the service can complete the 2FA verification.

    Raises
        HTTPException 401: if the challenge is invalid or expired.
    """
    try:
        payload = jwt.decode(
            body.challenge,
            settings.secret_key,
            algorithms=["HS256"],
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=401,
            detail="2FA challenge has expired",
        ) from exc
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=401,
            detail="Invalid 2FA challenge",
        ) from exc

    if payload.get("type") != "2fa_challenge":
        raise HTTPException(status_code=401, detail="Invalid challenge type")

    user_repo = UserRepository()
    user = await user_repo.get(
        id=UUID(payload["sub"]),
        tenant_id=UUID(payload["tenant_id"]),
        session=db,
    )
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="User is inactive")

    return user


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/enroll", response_model=TwoFAEnrollResponse)
async def enroll_2fa(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    totp_service: TotpService = Depends(get_totp_service),
) -> dict:
    """Enroll the authenticated user in 2FA.

    Returns an ``otpauth_uri`` (for QR code) and the plaintext ``secret``
    (for manual entry).  The user **must** call ``/confirm`` with a valid
    TOTP code afterwards to actually enable 2FA.
    """
    return await totp_service.enroll(current_user, db)


@router.post("/confirm", response_model=MessageResponse)
async def confirm_2fa(
    body: TwoFAConfirmRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    totp_service: TotpService = Depends(get_totp_service),
) -> dict:
    """Confirm 2FA enrollment with a TOTP code.

    If the code is valid, ``totp_enabled`` is set to ``True`` for the
    authenticated user.  Future logins will require a second factor.
    """
    ok = await totp_service.confirm(current_user, body.code, db)
    if not ok:
        raise HTTPException(
            status_code=400,
            detail="Invalid TOTP code — 2FA not enabled",
        )
    return MessageResponse(message="2FA enabled successfully").model_dump()


@router.post("/verify", response_model=TokenPair)
async def verify_2fa(
    body: TwoFAVerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_challenge),
    totp_service: TotpService = Depends(get_totp_service),
    token_service: TokenService = Depends(get_token_service),
) -> dict:
    """Complete 2FA verification and obtain a token pair.

    Expects a ``challenge`` JWT (obtained after password validation) and
    a valid TOTP ``code``.  Returns ``access_token`` + ``refresh_token``
    on success.
    """
    try:
        return await totp_service.verify_and_issue(
            user=current_user,
            challenge_token=body.challenge,
            code=body.code,
            token_service=token_service,
            session=db,
        )
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
