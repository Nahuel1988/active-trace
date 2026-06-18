"""TokenService — emisión, rotación y revocación de tokens JWT + refresh.

Uso::

    from app.services.token_service import TokenService, AuthError
    from app.repositories.refresh_token_repository import RefreshTokenRepository

    service = TokenService(refresh_token_repo=RefreshTokenRepository())
    pair = await service.issue_token_pair(user=user, session=db_session)

Dependencias:
    - RefreshTokenRepository: persistencia de tokens refresh.
    - app.core.security.encode_access_token: emisión de JWT.
    - app.core.security.generate_opaque_token / hash_token: refresh tokens.
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.security import (
    encode_access_token,
    generate_opaque_token,
    hash_token,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository


class AuthError(Exception):
    """Excepción de dominio para errores de autenticación.

    Attributes:
        status_code: Código HTTP (ej: 401).
        detail: Mensaje descriptivo para el cliente.
    """

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class TokenService:
    """Servicio de emisión, rotación y revocación de tokens.

    Flujo típico:
        1. issue_token_pair → login.
        2. rotate_refresh → refresh automático (sliding session).
        3. revoke_session → logout explícito.

    Principios:
        - Refresh tokens se persisten como hash (SHA-256), nunca en claro.
        - Los tokens se agrupan por *family_id* para detección de replay.
        - Si se detecta reuso, se revoca toda la familia (ataque mitigado).
    """

    def __init__(self, refresh_token_repo: RefreshTokenRepository) -> None:
        self._repo = refresh_token_repo

    async def issue_token_pair(
        self,
        user: User,
        session: AsyncSession,
        roles: list[str] | None = None,
    ) -> dict:
        """Emite un par access token (JWT) + refresh token (opaco).

        Args:
            user: Usuario autenticado (se usa **id**, **tenant_id**).
            session: Sesión de base de datos async.
            roles: Lista de roles del usuario (opcional; defaults a []).

        Returns:
            ``{"access_token": str, "refresh_token": str, "token_type": "bearer"}``
        """
        settings = Settings()
        now = datetime.now(timezone.utc)

        # 1. Access token JWT
        access_token = encode_access_token(
            sub=str(user.id),
            tenant_id=str(user.tenant_id),
            roles=roles or [],
        )

        # 2. Opaque refresh token + hash
        raw_token = generate_opaque_token()
        token_hash_value = hash_token(raw_token)

        # 3. Persistir refresh token
        refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=token_hash_value,
            family_id=uuid.uuid4(),
            expires_at=now + timedelta(days=settings.refresh_token_expire_days),
            tenant_id=user.tenant_id,
        )
        await self._repo.create(obj=refresh_token, session=session)

        return {
            "access_token": access_token,
            "refresh_token": raw_token,
            "token_type": "bearer",
        }

    async def rotate_refresh(
        self,
        raw_token: str,
        tenant_id: uuid.UUID,
        session: AsyncSession,
    ) -> dict:
        """Rota un refresh token: revoca el actual y emite uno nuevo.

        El nuevo token pertenece a la **misma familia** que el anterior
        para mantener la trazabilidad de la sesión.

        Args:
            raw_token: Token refresh en claro.
            tenant_id: UUID del tenant (scope de búsqueda).
            session: Sesión de base de datos async.

        Returns:
            ``{"access_token": str, "refresh_token": str, "token_type": "bearer"}``

        Raises:
            AuthError: 401 si el token es inválido, está revocado o expirado.
        """
        settings = Settings()
        now = datetime.now(timezone.utc)

        # 1. Hash + búsqueda
        token_hash_value = hash_token(raw_token)
        existing = await self._repo.get_by_hash(
            token_hash=token_hash_value,
            tenant_id=tenant_id,
            session=session,
        )

        if existing is None:
            msg = "Invalid or expired refresh token"
            raise AuthError(status_code=401, detail=msg)

        # 2. Reuse detection — token ya revocado → ataque de replay
        if existing.revoked_at is not None:
            # Revocar toda la familia: el atacante tiene un token comprometido
            await self._repo.revoke_family(
                family_id=existing.family_id,
                tenant_id=tenant_id,
                session=session,
            )
            msg = "Refresh token revoked"
            raise AuthError(status_code=401, detail=msg)

        # 3. Verificar expiración
        if existing.expires_at < now:
            msg = "Refresh token expired"
            raise AuthError(status_code=401, detail=msg)

        # 4. Revocar el token actual
        await self._repo.revoke(
            id=existing.id,
            tenant_id=tenant_id,
            session=session,
        )

        # 5. Emitir nuevo access token
        access_token = encode_access_token(
            sub=str(existing.user_id),
            tenant_id=str(tenant_id),
            roles=[],
        )

        # 6. Generar y persistir nuevo refresh token (misma familia)
        new_raw_token = generate_opaque_token()
        new_hash = hash_token(new_raw_token)

        new_refresh = RefreshToken(
            user_id=existing.user_id,
            token_hash=new_hash,
            family_id=existing.family_id,
            expires_at=now + timedelta(days=settings.refresh_token_expire_days),
            tenant_id=tenant_id,
        )
        await self._repo.create(obj=new_refresh, session=session)

        return {
            "access_token": access_token,
            "refresh_token": new_raw_token,
            "token_type": "bearer",
        }

    async def revoke_session(
        self,
        raw_token: str,
        tenant_id: uuid.UUID,
        session: AsyncSession,
    ) -> bool:
        """Revoca toda la familia de un refresh token (logout).

        Invalida el token actual y todos sus hermanos de familia,
        impidiendo cualquier rotación futura.

        Args:
            raw_token: Token refresh en claro.
            tenant_id: UUID del tenant.
            session: Sesión de base de datos async.

        Returns:
            ``True`` si se revocó al menos un token, ``False`` si el token
            no existe.
        """
        token_hash_value = hash_token(raw_token)
        existing = await self._repo.get_by_hash(
            token_hash=token_hash_value,
            tenant_id=tenant_id,
            session=session,
        )

        if existing is None:
            return False

        count = await self._repo.revoke_family(
            family_id=existing.family_id,
            tenant_id=tenant_id,
            session=session,
        )
        return count > 0
