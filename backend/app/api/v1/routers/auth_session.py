"""Auth session router — login, refresh, logout.

Endpoints:
    - ``POST /api/auth/login``  — authenticate + issue token pair (or 2FA challenge)
    - ``POST /api/auth/refresh`` — rotate refresh token (sliding session)
    - ``POST /api/auth/logout``  — revoke refresh token family

Business logic lives in ``AuthService`` and ``TokenService``; this router
only wires dependencies.

Cookie contract (D-01):
    The refresh token travels as an httpOnly cookie named ``rt``.
    The access token is returned in the JSON body and stored in memory by
    the frontend (never in localStorage).
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    CurrentUser,
    get_auth_service,
    get_current_user,
    get_db,
    get_token_service,
    get_totp_service,
)
from app.core.rate_limit import LOGIN_RATE_LIMIT, limiter, login_key_func
from app.core.security import decode_token
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
)
from app.services.auth_service import AuthService
from app.services.permission_service import PermissionService
from app.services.token_service import TokenService
from app.services.totp_service import TotpService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])

_REFRESH_COOKIE = "rt"
_COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # 7 days


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=raw_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=_COOKIE_MAX_AGE,
        path="/",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=_REFRESH_COOKIE, path="/")


def _user_from_access_token(access_token: str, permissions: list[str] | None = None) -> dict:
    """Build the user payload the frontend expects from JWT claims."""
    claims = decode_token(access_token)
    return {
        "user_id": claims["sub"],
        "tenant_id": claims["tenant_id"],
        "roles": claims.get("roles", []),
        "permissions": permissions or [],
    }


async def _fetch_permissions(access_token: str, db: AsyncSession) -> list[str]:
    """Resolve effective permission codes for the user in the access token."""
    claims = decode_token(access_token)
    service = PermissionService()
    effective = await service.get_effective_permissions(
        user_id=UUID(claims["sub"]),
        tenant_id=UUID(claims["tenant_id"]),
        session=db,
    )
    return list(effective.keys())


async def _resolve_tenant_id(db: AsyncSession):
    # FIXME: resolve tenant from subdomain/header (multi-tenancy)
    # DEV fallback: use first tenant in the DB
    row = await db.execute(text("SELECT id FROM tenant LIMIT 1"))
    tenant = row.fetchone()
    return tenant.id if tenant else None


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


@router.post("/api/auth/login")
@limiter.limit(LOGIN_RATE_LIMIT, key_func=login_key_func)
async def login(
    request: Request,
    response: Response,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
    totp_service: TotpService = Depends(get_totp_service),
    token_service: TokenService = Depends(get_token_service),
) -> dict:
    """Authenticate user and return access token + user payload (or 2FA challenge).

    The refresh token is set as an httpOnly cookie (not in the response body).
    Rate-limited by IP + email (5 req/min).
    """
    request.state.login_email = body.email
    tenant_id = await _resolve_tenant_id(db)

    result = await auth_service.login(
        email=body.email,
        password=body.password,
        tenant_id=tenant_id,  # type: ignore[arg-type]
        totp_service=totp_service,
        token_service=token_service,
        session=db,
    )

    # 2FA required — return challenge token, no cookie yet
    if result.get("type") == "2fa_challenge":
        return {
            "requires_2fa": True,
            "access_token": result["challenge"],
            "user": None,
        }

    _set_refresh_cookie(response, result["refresh_token"])
    access_token = result["access_token"]
    permissions = await _fetch_permissions(access_token, db)
    return {
        "access_token": access_token,
        "user": _user_from_access_token(access_token, permissions=permissions),
    }


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------


@router.post("/api/auth/refresh")
async def refresh(
    response: Response,
    db: AsyncSession = Depends(get_db),
    token_service: TokenService = Depends(get_token_service),
    rt: str | None = Cookie(default=None),
) -> dict:
    """Rotate refresh token and return new access token + user payload.

    Reads the refresh token from the httpOnly cookie ``rt``.
    """
    if not rt:
        raise HTTPException(status_code=401, detail="No refresh token")

    tenant_id = await _resolve_tenant_id(db)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="No tenant")

    result = await token_service.rotate_refresh(
        raw_token=rt,
        tenant_id=tenant_id,
        session=db,
    )

    _set_refresh_cookie(response, result["refresh_token"])
    access_token = result["access_token"]
    permissions = await _fetch_permissions(access_token, db)
    return {
        "access_token": access_token,
        "user": _user_from_access_token(access_token, permissions=permissions),
    }


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


@router.post("/api/auth/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    token_service: TokenService = Depends(get_token_service),
    rt: str | None = Cookie(default=None),
) -> dict:
    """Revoke refresh token family (logout).

    Reads the refresh token from the httpOnly cookie ``rt``.
    """
    if rt:
        await token_service.revoke_session(
            raw_token=rt,
            tenant_id=current_user.tenant_id,
            session=db,
        )
    _clear_refresh_cookie(response)
    return MessageResponse(message="Session closed").model_dump()
