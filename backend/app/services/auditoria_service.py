"""AuditoriaService — lógica de scope y orquestación de consultas de auditoría.

Tres responsabilidades:
1. Calcular el ``scope_actor_id`` a partir de los roles del usuario
   (ADMIN/FINANZAS → global, COORDINADOR → ``(propio)``).
2. Combinar ese scope con los filtros del DTO, garantizando que el scope
   prevalezca sobre cualquier filtro enviado por el cliente.
3. Delegar al ``AuditLogRepository`` para las consultas y agregaciones.

Regla de seguridad: el ``scope_actor_id`` se deriva SOLO de los roles de la
sesión (``PermissionGrant.scope``). Nunca del input del cliente.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import PermissionGrant
from app.repositories.audit_log_repository import AuditLogRepository


class AuditoriaService:
    """Service de consultas de auditoría con scope por rol."""

    def __init__(self) -> None:
        self._repo = AuditLogRepository()

    def _resolve_scope_actor_id(
        self,
        grant: PermissionGrant,
        current_user: object,
    ) -> UUID | None:
        """Determina el alcance de visibilidad según el permiso concedido.

        Args:
            grant: Concesión de permiso ``auditoria:ver`` con su scope.
            current_user: Usuario autenticado (con atributo ``id``).

        Returns:
            ``None`` si el scope es ``"global"`` (ADMIN/FINANZAS).
            ``current_user.id`` si el scope es ``"propio"`` (COORDINADOR).
        """
        if grant.scope == "global":
            return None
        # scope == "propio" — acotado al usuario actual
        user_id: UUID = current_user.id  # type: ignore[union-attr]
        return user_id

    # ── Panel F9.1 ──────────────────────────────────────────────────────────

    async def get_acciones_por_dia(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        grant: PermissionGrant,
        current_user: object,
        desde: datetime | None = None,
        hasta: datetime | None = None,
    ) -> list[dict]:
        """Acciones por día (serie temporal)."""
        scope_actor_id = self._resolve_scope_actor_id(grant, current_user)
        return await self._repo.aggregate_acciones_por_dia(
            tenant_id=tenant_id,
            session=session,
            scope_actor_id=scope_actor_id,
            desde=desde,
            hasta=hasta,
        )

    async def get_comunicaciones_por_docente(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        grant: PermissionGrant,
        current_user: object,
        desde: datetime | None = None,
        hasta: datetime | None = None,
    ) -> list[dict]:
        """Estado de comunicaciones por docente."""
        scope_actor_id = self._resolve_scope_actor_id(grant, current_user)
        return await self._repo.aggregate_comunicaciones_por_docente(
            tenant_id=tenant_id,
            session=session,
            scope_actor_id=scope_actor_id,
            desde=desde,
            hasta=hasta,
        )

    async def get_interacciones(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        grant: PermissionGrant,
        current_user: object,
        desde: datetime | None = None,
        hasta: datetime | None = None,
    ) -> list[dict]:
        """Interacciones por docente × materia."""
        scope_actor_id = self._resolve_scope_actor_id(grant, current_user)
        return await self._repo.aggregate_interacciones_docente_materia(
            tenant_id=tenant_id,
            session=session,
            scope_actor_id=scope_actor_id,
            desde=desde,
            hasta=hasta,
        )

    async def get_ultimas_acciones(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        grant: PermissionGrant,
        current_user: object,
        limit: int = 200,
        offset: int = 0,
    ) -> list[dict]:
        """Últimas N acciones (log resumido del panel)."""
        scope_actor_id = self._resolve_scope_actor_id(grant, current_user)
        results = await self._repo.list_filtrado(
            tenant_id=tenant_id,
            session=session,
            scope_actor_id=scope_actor_id,
            limit=limit,
            offset=offset,
        )
        return [
            {
                "id": r.id,
                "fecha_hora": r.fecha_hora,
                "actor_id": r.actor_id,
                "materia_id": r.materia_id,
                "accion": r.accion,
                "filas_afectadas": r.filas_afectadas,
                "ip": r.ip,
                "user_agent": r.user_agent,
            }
            for r in results
        ]

    # ── Log completo F9.2 ───────────────────────────────────────────────────

    async def get_log(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        grant: PermissionGrant,
        current_user: object,
        desde: datetime | None = None,
        hasta: datetime | None = None,
        materia_id: UUID | None = None,
        actor_id: UUID | None = None,
        accion: str | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[dict]:
        """Log completo de auditoría con filtros combinados + scope.

        El scope ``(propio)`` prevalece sobre cualquier ``actor_id`` enviado
        por el cliente (seguridad: coordinador no puede ver acciones ajenas
        aunque filtre por otro actor).
        """
        scope_actor_id = self._resolve_scope_actor_id(grant, current_user)

        # Si el usuario tiene scope propio y envió un actor_id distinto,
        # el scope prevalece (el coordinador no puede ver lo ajeno)
        effective_actor = scope_actor_id or actor_id

        results = await self._repo.list_filtrado(
            tenant_id=tenant_id,
            session=session,
            scope_actor_id=scope_actor_id,
            desde=desde,
            hasta=hasta,
            materia_id=materia_id,
            accion=accion,
            limit=limit,
            offset=offset,
        )
        return [
            {
                "id": r.id,
                "fecha_hora": r.fecha_hora,
                "actor_id": r.actor_id,
                "materia_id": r.materia_id,
                "accion": r.accion,
                "detalle": r.detalle,
                "filas_afectadas": r.filas_afectadas,
                "ip": r.ip,
                "user_agent": r.user_agent,
            }
            for r in results
        ]
