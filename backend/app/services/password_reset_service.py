"""PasswordResetService — gestión de reseteo de contraseña.

Flujo:
    1. forgot(email): genera token opaco, persiste hash, envía email.
    2. reset(token, new_password): valida token, cambia password, revoca sesiones.

El EmailSender es inyectado para permitir tests con fake.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.security import email_lookup_hash, generate_opaque_token, hash_password, hash_token
from app.models.password_reset_token import PasswordResetToken
from app.repositories.password_reset_token_repository import PasswordResetTokenRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository


# ---------------------------------------------------------------------------
# Email sender protocol (inyectable)
# ---------------------------------------------------------------------------


class EmailSender(ABC):
    """Protocolo abstracto para envío de emails."""

    @abstractmethod
    async def send(self, to: str, subject: str, body: str) -> None:
        """Envía un email. La implementación concreta decide el método."""


# ---------------------------------------------------------------------------
# PasswordResetService
# ---------------------------------------------------------------------------


class PasswordResetService:
    """Servicio de reseteo de contraseña con uniformidad de respuesta.

    El método ``forgot`` SIEMPRE retorna el mismo mensaje (200) para
    prevenir enumeración de emails. El token en DB se almacena solo
    como hash SHA-256, nunca en texto plano.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        reset_token_repo: PasswordResetTokenRepository,
        email_sender: EmailSender,
        refresh_token_repo: RefreshTokenRepository | None = None,
    ) -> None:
        self._user_repo = user_repo
        self._reset_token_repo = reset_token_repo
        self._email_sender = email_sender
        self._refresh_token_repo = refresh_token_repo
        self._settings = Settings()

    async def forgot(self, email: str, tenant_id: UUID, session: AsyncSession) -> dict:
        """Procesa una solicitud de reseteo de contraseña.

        Args:
            email: Email del usuario (en texto plano, se normaliza internamente).
            tenant_id: UUID del tenant al que pertenece el usuario.
            session: Sesión de base de datos async.

        Returns:
            Siempre ``{"message": "If the email exists, a reset link has been sent."}``
            independientemente de si el email existe o no.
        """
        email_lk = email_lookup_hash(email)
        user = await self._user_repo.get_active_by_email_lookup(
            tenant_id=tenant_id,
            email_lookup=email_lk,
            session=session,
        )

        if user is not None:
            raw_token = generate_opaque_token()
            token_hashed = hash_token(raw_token)
            expires_at = datetime.now(timezone.utc) + timedelta(
                minutes=self._settings.password_reset_expire_minutes,
            )

            prt = PasswordResetToken(
                user_id=user.id,
                token_hash=token_hashed,
                expires_at=expires_at,
                tenant_id=tenant_id,
            )
            await self._reset_token_repo.create(obj=prt, session=session)

            await self._email_sender.send(
                to=email,
                subject="Password Reset",
                body=f"Your password reset token is: {raw_token}",
            )

        return {"message": "If the email exists, a reset link has been sent."}

    async def reset(self, token: str, new_password: str, tenant_id: UUID, session: AsyncSession) -> dict:
        """Procesa un reseteo de contraseña con un token.

        Args:
            token: Token opaco recibido por email (en texto plano).
            new_password: Nueva contraseña en texto plano.
            tenant_id: UUID del tenant.
            session: Sesión de base de datos async.

        Returns:
            ``{"message": "Password reset successfully."}`` si el token es válido.

        Raises:
            HTTPException 400: si el token no existe, ya fue usado o expiró.
        """
        from fastapi import HTTPException

        token_hashed = hash_token(token)
        stored = await self._reset_token_repo.get_by_hash(
            token_hash=token_hashed,
            tenant_id=tenant_id,
            session=session,
        )

        if stored is None:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token.")

        if stored.used_at is not None:
            raise HTTPException(status_code=400, detail="Reset token has already been used.")

        if stored.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Reset token has expired.")

        # Set new password
        new_hash = hash_password(new_password)
        user = await self._user_repo.get(
            id=stored.user_id,
            tenant_id=tenant_id,
            session=session,
        )
        if user is None:
            raise HTTPException(status_code=400, detail="User not found.")

        user.password_hash = new_hash
        await session.flush()

        # Mark token as used
        await self._reset_token_repo.mark_used(
            id=stored.id,
            tenant_id=tenant_id,
            session=session,
        )

        # Revoke all refresh token families for this user
        if self._refresh_token_repo is not None:
            await self._refresh_token_repo.revoke_all_for_user(
                user_id=user.id,
                tenant_id=tenant_id,
                session=session,
            )

        return {"message": "Password reset successfully."}
