"""Dependencias globales de FastAPI.

Inyectan settings, sesión de BD, repositorios, servicios y el usuario
autenticado (``get_current_user``).
"""

from collections.abc import AsyncGenerator
from functools import lru_cache
from uuid import UUID

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.core.database import create_engine, create_session_factory
from app.core.security import decode_token


# ---------------------------------------------------------------------------
# Settings, engine, session
# ---------------------------------------------------------------------------


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_engine() -> AsyncEngine:
    return create_engine(get_settings())


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return create_session_factory(get_engine())


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        await session.close()


# ---------------------------------------------------------------------------
# Servicios
# ---------------------------------------------------------------------------


def get_auth_service() -> "AuthService":  # noqa: F821
    """Build an AuthService with its repository."""
    from app.repositories.user_repository import UserRepository
    from app.services.auth_service import AuthService

    return AuthService(user_repo=UserRepository())


def get_token_service() -> "TokenService":  # noqa: F821
    """Build a TokenService with its repository."""
    from app.repositories.refresh_token_repository import RefreshTokenRepository
    from app.services.token_service import TokenService

    return TokenService(refresh_token_repo=RefreshTokenRepository())


def get_totp_service() -> "TotpService":  # noqa: F821
    """Build a TotpService with its repository and encryption."""
    from app.core.security import get_encryption_service
    from app.repositories.totp_secret_repository import TotpSecretRepository
    from app.services.totp_service import TotpService

    return TotpService(
        totp_repo=TotpSecretRepository(),
        encryption_service=get_encryption_service(),
    )


# ---------------------------------------------------------------------------
# Auth — current user
# ---------------------------------------------------------------------------


async def get_current_user(  # noqa: RUF029
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> "User":  # noqa: F821
    """Extract the authenticated user from the JWT access token.

    Reads the ``Authorization: Bearer <token>`` header, decodes the
    token, and returns the corresponding ``User`` object.

    **Security invariant**: identity is ALWAYS taken from the JWT, never
    from URL / body / query parameters.

    Raises
        HTTPException 401: if the token is missing, invalid, or the
            user does not exist / is inactive.
    """
    if authorization is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format",
        )

    token = authorization.removeprefix("Bearer ")
    try:
        payload = decode_token(token)
    except Exception as exc:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token",
        ) from exc

    from app.models.user import User
    from app.repositories.user_repository import UserRepository

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
