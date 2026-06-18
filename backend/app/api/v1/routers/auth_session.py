"""Auth session router — login, refresh, logout.

Endpoints:
    - ``POST /api/auth/login``  — authenticate + issue token pair (or 2FA challenge)
    - ``POST /api/auth/refresh`` — rotate refresh token (sliding session)
    - ``POST /api/auth/logout``  — revoke refresh token family

Business logic lives in ``AuthService`` and ``TokenService``; this router
only wires dependencies.
"""

import logging
from typing import Union

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    get_auth_service,
    get_current_user,
    get_db,
    get_token_service,
    get_totp_service,
)
from app.core.rate_limit import LOGIN_RATE_LIMIT, limiter, login_key_func
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    TokenPair,
    TwoFAChallenge,
)
from app.services.auth_service import AuthService
from app.services.token_service import TokenService
from app.services.totp_service import TotpService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


@router.post("/api/auth/login", response_model=Union[TokenPair, TwoFAChallenge])
@limiter.limit(LOGIN_RATE_LIMIT, key_func=login_key_func)
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
    totp_service: TotpService = Depends(get_totp_service),
    token_service: TokenService = Depends(get_token_service),
) -> dict:
    """Authenticate user and return token pair or 2FA challenge.

    Rate-limited by IP + email (5 req/min).
    """
    request.state.login_email = body.email
    # FIXME: resolve tenant from subdomain/header (multi-tenancy)
    tenant_id = None
    result = await auth_service.login(
        email=body.email,
        password=body.password,
        tenant_id=tenant_id,  # type: ignore[arg-type]
        totp_service=totp_service,
        token_service=token_service,
        session=db,
    )
    return result


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------


@router.post("/api/auth/refresh", response_model=TokenPair)
async def refresh(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    token_service: TokenService = Depends(get_token_service),
) -> dict:
    """Rotate refresh token and return a new token pair."""
    # FIXME: resolve tenant from subdomain/header (multi-tenancy)
    result = await token_service.rotate_refresh(
        raw_token=body.refresh_token,
        tenant_id=None,  # type: ignore[arg-type]
        session=db,
    )
    return result


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


@router.post("/api/auth/logout", response_model=MessageResponse)
async def logout(
    body: LogoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    token_service: TokenService = Depends(get_token_service),
) -> dict:
    """Revoke refresh token family (logout)."""
    await token_service.revoke_session(
        raw_token=body.refresh_token,
        tenant_id=current_user.tenant_id,
        session=db,
    )
    return MessageResponse(message="Session closed").model_dump()
