"""Audit context, helper y decorator para el registro de auditoría.

Este módulo provee:
- ``AuditContext``: dataclass inmutable con los datos del actor (identidad,
  tenant, IP, user-agent, impersonación).
- ``audit_action``: función async que construye y persiste un ``AuditLog``
  a partir de un ``AuditContext``.
- ``audited``: decorator para routers FastAPI que extrae el contexto del
  ``Request`` y registra automáticamente la acción tras una respuesta
  exitosa.

Uso del decorator::

    from app.core.audit import AuditCodes, audited

    @router.post("/algo")
    @audited(AuditCodes.MI_ACCION)
    async def mi_endpoint(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> dict:
        ...

Uso manual (sin decorator) — construir AuditContext desde get_current_user::

    from app.core.audit import AuditCodes, AuditContext, audit_action
    from app.core.dependencies import CurrentUser, get_current_user

    @router.post("/mi-accion")
    async def mi_endpoint(
        request: Request,
        current_user: CurrentUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> dict:
        # ... lógica de negocio ...
        ctx = AuditContext(
            actor_id=current_user.actor_id,
            tenant_id=current_user.tenant_id,
            ip=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", ""),
            impersonado_id=current_user.id if current_user.impersonated else None,
        )
        await audit_action(
            ctx=ctx,
            accion=AuditCodes.MI_ACCION,
            detalle={"key": "value"},
            session=db,
        )
        return {"status": "ok"}
"""

import functools
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_codes import AuditCodes  # noqa: F401 — re-export for convenience
from app.models.audit_log import AuditLog
from app.repositories.audit_log_repository import AuditLogRepository


@dataclass(frozen=True)
class AuditContext:
    """Contexto inmutable que identifica quién realiza la acción auditada.

    Args:
        actor_id: UUID del usuario que ejecuta la acción.
        tenant_id: UUID del tenant al que pertenece el actor.
        ip: Dirección IP del cliente.
        user_agent: User-agent del cliente.
        impersonado_id: UUID del usuario impersonado, si aplica.
    """

    actor_id: UUID
    tenant_id: UUID
    ip: str
    user_agent: str
    impersonado_id: UUID | None = None


async def audit_action(
    *,
    ctx: AuditContext,
    accion: str,
    detalle: dict,
    session: AsyncSession,
    filas_afectadas: int = 0,
    materia_id: UUID | None = None,
    repo: AuditLogRepository | None = None,
) -> AuditLog:
    """Construye y persiste un registro de auditoría.

    Args:
        ctx: Contexto del actor que ejecuta la acción.
        accion: Código de acción (usar ``AuditCodes``).
        detalle: Diccionario con datos adicionales de la acción.
        session: Sesión async de SQLAlchemy.
        filas_afectadas: Cantidad de filas afectadas (default 0).
        materia_id: ID de materia asociada (opcional).
        repo: Repositorio a usar; si no se pasa, se crea uno nuevo.

    Returns:
        El ``AuditLog`` persistido (con id y fecha_hora generados).
    """
    if repo is None:
        repo = AuditLogRepository()

    entry = AuditLog(
        tenant_id=ctx.tenant_id,
        actor_id=ctx.actor_id,
        impersonado_id=ctx.impersonado_id,
        accion=accion,
        detalle=detalle,
        filas_afectadas=filas_afectadas,
        materia_id=materia_id,
        ip=ctx.ip,
        user_agent=ctx.user_agent,
    )
    return await repo.add(entry=entry, session=session)


def audited(accion: str) -> Callable:
    """Decorator factory: registra automaticamente una accion en el audit log
    tras una respuesta exitosa del endpoint.

    El decorator extrae el ``AuditContext`` del ``Request`` y del
    ``current_user`` (inyectado via ``get_current_user``) y ejecuta
    ``audit_action`` SOLO si la funcion completa sin lanzar excepcion.

    La cantidad de filas afectadas se obtiene del campo ``_filas_afectadas``
    del objeto response, o 0 por defecto.

    Args:
        accion: Codigo de accion (usar constantes de ``AuditCodes``).

    Returns:
        Decorator que envuelve la funcion async del endpoint.

    Example::

        @router.post("/importar")
        @audited(AuditCodes.CALIFICACIONES_IMPORTAR)
        async def importar(
            request: Request,
            current_user: User = Depends(get_current_user),
            db: AsyncSession = Depends(get_db),
        ) -> dict:
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            request: Request | None = None
            current_user: Any = None
            session: AsyncSession | None = None

            for key, value in kwargs.items():
                if isinstance(value, Request):
                    request = value
                elif key == "current_user":
                    current_user = value
                elif key in ("db", "session"):
                    session = value

            # Call the original function — if it raises, no audit is recorded
            response = await func(*args, **kwargs)

            # Only record audit on success
            if (
                request is not None
                and current_user is not None
                and session is not None
            ):
                actor_id: UUID
                tenant_id: UUID
                impersonado_id: UUID | None = None

                if hasattr(current_user, "actor_id") and current_user.actor_id is not None:  # type: ignore[attr-defined]
                    actor_id = current_user.actor_id  # type: ignore[attr-defined]
                else:
                    actor_id = current_user.id  # type: ignore[attr-defined]

                tenant_id = current_user.tenant_id  # type: ignore[attr-defined]

                if getattr(current_user, "impersonated", False):
                    impersonado_id = current_user.id  # type: ignore[attr-defined]

                ctx = AuditContext(
                    actor_id=actor_id,
                    tenant_id=tenant_id,
                    ip=request.client.host if request.client else "unknown",
                    user_agent=request.headers.get("user-agent", ""),
                    impersonado_id=impersonado_id,
                )

                if isinstance(response, dict):
                    filas_afectadas = response.get("_filas_afectadas", 0)
                else:
                    filas_afectadas = getattr(response, "_filas_afectadas", 0)

                await audit_action(
                    ctx=ctx,
                    accion=accion,
                    detalle={},
                    filas_afectadas=filas_afectadas,
                    session=session,
                )

            return response

        return wrapper

    return decorator
