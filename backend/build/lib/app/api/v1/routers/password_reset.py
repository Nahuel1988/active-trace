"""Password reset router — endpoints de reseteo de contraseña.

Endpoints:

    POST /api/auth/forgot   → Solicitud de reseteo de contraseña.
    POST /api/auth/reset    → Ejecución de reseteo con token.

Ambos endpoints extraen el tenant del header ``X-Tenant-ID``.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.repositories.password_reset_token_repository import (
    PasswordResetTokenRepository,
)
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import ForgotRequest, MessageResponse, ResetRequest
from app.services.password_reset_service import PasswordResetService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth"], prefix="/api/auth")


# ---------------------------------------------------------------------------
# Email sender temporal — loguea en lugar de enviar
# ---------------------------------------------------------------------------


class _LoggingEmailSender:
    """EmailSender temporal que logea los emails en lugar de enviarlos.

    Será reemplazado por una implementación real (SMTP / SendGrid / etc.)
    cuando se integre el módulo de comunicaciones.
    """

    async def send(self, to: str, subject: str, body: str) -> None:
        logger.info("EMAIL TO=%s | SUBJECT=%s | BODY=%s", to, subject, body)


# ---------------------------------------------------------------------------
# Factory del servicio
# ---------------------------------------------------------------------------


def _get_password_reset_service() -> PasswordResetService:
    """Construye un ``PasswordResetService`` con sus dependencias reales."""
    return PasswordResetService(
        user_repo=UserRepository(),
        reset_token_repo=PasswordResetTokenRepository(),
        email_sender=_LoggingEmailSender(),
        refresh_token_repo=RefreshTokenRepository(),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/forgot", response_model=MessageResponse)
async def forgot_password(
    body: ForgotRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Solicita un token de reseteo de contraseña.

    El tenant_id se extrae del header ``X-Tenant-ID``.
    La respuesta es SIEMPRE 200 con el mismo mensaje para evitar
    enumeración de emails.
    """
    tenant_id_raw = request.headers.get("X-Tenant-ID", "")
    tenant_id = UUID(tenant_id_raw) if tenant_id_raw else UUID(int=0)

    service = _get_password_reset_service()
    return await service.forgot(email=body.email, tenant_id=tenant_id, session=db)


@router.post("/reset", response_model=MessageResponse)
async def reset_password(
    body: ResetRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Resetea la contraseña usando un token válido.

    El tenant_id se extrae del header ``X-Tenant-ID``.
    Si el token es inválido, usado o expirado retorna 400.
    """
    tenant_id_raw = request.headers.get("X-Tenant-ID", "")
    tenant_id = UUID(tenant_id_raw) if tenant_id_raw else UUID(int=0)

    service = _get_password_reset_service()
    return await service.reset(
        token=body.token,
        new_password=body.new_password,
        tenant_id=tenant_id,
        session=db,
    )
