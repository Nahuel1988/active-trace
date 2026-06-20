"""Dependencias globales de FastAPI.

Inyectan settings, sesión de BD, repositorios, servicios y el usuario
autenticado (``get_current_user``).
"""

from collections.abc import AsyncGenerator
from functools import lru_cache
from typing import Any
from uuid import UUID

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.core.database import create_engine, create_session_factory
from app.core.security import decode_token


class CurrentUser:
    """Usuario autenticado extendido con información de impersonación.

    Envuelve una instancia de ``User`` (SQLAlchemy) y delega el acceso a
    atributos del modelo ORM (``id``, ``tenant_id``, ``is_active``, etc.)
    al objeto subyacente.  Esto permite que servicios existentes que reciben
    ``current_user: User`` sigan funcionando sin cambios.

    Atributos adicionales (no ORM):
        impersonated: ``True`` si la sesión actual es de impersonación.
        actor_id: UUID del usuario real que ejecuta la acción (para
            impersonación; en sesiones normales es igual a ``user.id``).

    Uso::

        async def mi_endpoint(
            current_user: CurrentUser = Depends(get_current_user),
        ) -> dict:
            if current_user.impersonated:
                logger.info("Operación como %s por %s", current_user.id, current_user.actor_id)
    """

    def __init__(
        self,
        user: Any,
        *,
        impersonated: bool = False,
        actor_id: UUID | None = None,
    ) -> None:
        object.__setattr__(self, "_user", user)
        object.__setattr__(self, "impersonated", impersonated)
        object.__setattr__(
            self,
            "actor_id",
            actor_id if actor_id is not None else user.id,
        )

    def __getattr__(self, name: str) -> Any:
        if name in ("impersonated", "actor_id", "_user"):
            return object.__getattribute__(self, name)
        return getattr(self._user, name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ("impersonated", "actor_id"):
            object.__setattr__(self, name, value)
        else:
            setattr(self._user, name, value)

    def __repr__(self) -> str:
        user_id = self._user.id
        flag = " [IMP]" if self.impersonated else ""
        return f"<CurrentUser id={user_id} actor={self.actor_id}{flag}>"


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
    """Yields an AsyncSession and commits on success, rolls back on error.

    Standard FastAPI + SQLAlchemy unit-of-work pattern: the session is
    committed after the request handler completes successfully, or rolled
    back if an exception escapes.
    """
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
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


async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> CurrentUser:
    """Extrae el usuario autenticado desde el JWT access token.

    Lee el header ``Authorization: Bearer <token>``, decodifica el token,
    carga el ``User`` desde la base de datos y lo envuelve en un
    ``CurrentUser`` con información de impersonación.

    **Security invariant**: la identidad SIEMPRE se toma del JWT, nunca
    de URL / body / query parameters.

    Raises
        HTTPException 401: si el token falta, es inválido, o el usuario
            no existe / está inactivo.
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

    impersonated = payload.get("impersonated", False)
    actor_id_raw = payload.get("actor_id")
    actor_id: UUID | None = UUID(actor_id_raw) if actor_id_raw else None

    return CurrentUser(
        user=user,
        impersonated=impersonated,
        actor_id=actor_id,
    )
