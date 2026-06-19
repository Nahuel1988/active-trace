"""AuditLogRepository — solo lectura (append-only) con métodos de agregación.

El registro de auditoría es append-only. Este repositorio:
- Hereda de ``BaseRepository[AuditLog]`` para acceso a la sesión y typing.
- Expone ``add`` (escritura) y múltiples métodos de **solo lectura**:
  ``list``, ``list_filtrado``, ``aggregate_acciones_por_dia``,
  ``aggregate_comunicaciones_por_docente``,
  ``aggregate_interacciones_docente_materia``.
- NO expone ``update``, ``delete``, ``soft_delete`` ni ninguna operación de
  modificación. La inmutabilidad se refuerza a nivel DB (reglas PostgreSQL).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    cast,
    Date,
    func,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.repositories.base import BaseRepository

#: Tope máximo de seguridad para limit en consultas de auditoría.
AUDIT_LOG_MAX_LIMIT = 1000


class AuditLogRepository(BaseRepository[AuditLog]):
    """Repositorio append-only para el registro de auditoría.

    Métodos de escritura:
    - ``add``: persistir una nueva entrada.

    Métodos de **solo lectura** (no modifican el estado):
    - ``list``: listado simple por tenant.
    - ``list_filtrado``: listado paginado con filtros opcionales + scope.
    - ``aggregate_acciones_por_dia``: conteo de acciones por día.
    - ``aggregate_comunicaciones_por_docente``: distribución de estados.
    - ``aggregate_interacciones_docente_materia``: conteo por actor×materia.

    Los métodos heredados ``update`` y ``soft_delete`` lanzan
    ``NotImplementedError`` porque la auditoría es inmutable.
    """

    def __init__(self) -> None:
        super().__init__(AuditLog)

    # ── Invariante: sin mutación ─────────────────────────────────────────────

    async def create(self, *args: object, **kwargs: object) -> object:  # type: ignore[explicit-any]
        msg = "AuditLogRepository does not support create — use add() instead (append-only)"
        raise NotImplementedError(msg)

    def update(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        msg = "AuditLogRepository does not support update (append-only)"
        raise NotImplementedError(msg)

    def soft_delete(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        msg = "AuditLogRepository does not support delete (append-only)"
        raise NotImplementedError(msg)

    # ── Escritura ────────────────────────────────────────────────────────────

    async def add(
        self,
        *,
        entry: AuditLog,
        session: AsyncSession,
    ) -> AuditLog:
        """Persiste una nueva entrada de auditoría.

        Args:
            entry: Instancia de ``AuditLog`` (sin persistir).
            session: Sesión async de SQLAlchemy.

        Returns:
            La misma entrada con ``id`` y ``fecha_hora`` generados.
        """
        session.add(entry)
        await session.flush()
        await session.refresh(entry)
        return entry

    # ── Lectura simple ──────────────────────────────────────────────────────

    async def list(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Retorna entradas de auditoría para un tenant, ordenadas por fecha.

        Args:
            tenant_id: UUID del tenant (scope obligatorio).
            session: Sesión async de SQLAlchemy.
            limit: Máximo de registros a retornar (default 50).
            offset: Desplazamiento para paginación (default 0).

        Returns:
            Lista de ``AuditLog`` del tenant, más recientes primero.
        """
        stmt = (
            select(self.model)
            .where(self.model.tenant_id == tenant_id)  # type: ignore[attr-defined]
            .order_by(self.model.fecha_hora.desc())     # type: ignore[attr-defined]
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    # ── Lectura con filtros ─────────────────────────────────────────────────

    async def list_filtrado(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        scope_actor_id: UUID | None = None,
        desde: datetime | None = None,
        hasta: datetime | None = None,
        materia_id: UUID | None = None,
        accion: str | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Listado paginado de auditoría con filtros opcionales + scope.

        Args:
            tenant_id: UUID del tenant (obligatorio — scope de fila).
            session: Sesión async de SQLAlchemy.
            scope_actor_id: Si se pasa, filtra SOLO registros cuyo
                ``actor_id`` coincida (scope ``(propio)``). ``None``
                devuelve todos los del tenant.
            desde: Filtro inicio de rango (inclusive).
            hasta: Filtro fin de rango (inclusive).
            materia_id: Filtra por materia específica.
            accion: Código de acción exacto.
            limit: Máx. registros (default 200, recortado a
                ``AUDIT_LOG_MAX_LIMIT``).
            offset: Desplazamiento para paginación.

        Returns:
            Lista de ``AuditLog`` que cumplen todos los filtros, más
            recientes primero.
        """
        safe_limit = min(limit, AUDIT_LOG_MAX_LIMIT)
        stmt = (
            select(self.model)
            .where(self.model.tenant_id == tenant_id)  # type: ignore[attr-defined]
            .order_by(self.model.fecha_hora.desc())     # type: ignore[attr-defined]
            .offset(offset)
            .limit(safe_limit)
        )

        if scope_actor_id is not None:
            stmt = stmt.where(self.model.actor_id == scope_actor_id)  # type: ignore[attr-defined]
        if desde is not None:
            stmt = stmt.where(self.model.fecha_hora >= desde)  # type: ignore[attr-defined]
        if hasta is not None:
            stmt = stmt.where(self.model.fecha_hora <= hasta)  # type: ignore[attr-defined]
        if materia_id is not None:
            stmt = stmt.where(self.model.materia_id == materia_id)  # type: ignore[attr-defined]
        if accion is not None:
            stmt = stmt.where(self.model.accion == accion)  # type: ignore[attr-defined]

        result = await session.execute(stmt)
        return list(result.scalars().all())

    # ── Agregaciones ────────────────────────────────────────────────────────

    async def aggregate_acciones_por_dia(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        scope_actor_id: UUID | None = None,
        desde: datetime | None = None,
        hasta: datetime | None = None,
    ) -> list[dict]:
        """Conteo de acciones por día calendario, ordenado ascendente.

        Args:
            tenant_id: UUID del tenant.
            session: Sesión async.
            scope_actor_id: Filtro opcional por actor.
            desde: Filtro inicio de rango.
            hasta: Filtro fin de rango.

        Returns:
            Lista de dicts ``{"fecha": date, "total": int}``.
        """
        fecha_col = cast(self.model.fecha_hora, Date)  # type: ignore[attr-defined]
        stmt = (
            select(fecha_col.label("fecha"), func.count().label("total"))
            .where(self.model.tenant_id == tenant_id)  # type: ignore[attr-defined]
            .group_by(fecha_col)
            .order_by(fecha_col)
        )

        if scope_actor_id is not None:
            stmt = stmt.where(self.model.actor_id == scope_actor_id)  # type: ignore[attr-defined]
        if desde is not None:
            stmt = stmt.where(self.model.fecha_hora >= desde)  # type: ignore[attr-defined]
        if hasta is not None:
            stmt = stmt.where(self.model.fecha_hora <= hasta)  # type: ignore[attr-defined]

        result = await session.execute(stmt)
        return [{"fecha": row.fecha, "total": row.total} for row in result]

    async def aggregate_comunicaciones_por_docente(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        scope_actor_id: UUID | None = None,
        desde: datetime | None = None,
        hasta: datetime | None = None,
    ) -> list[dict]:
        """Distribución de códigos de comunicación por actor.

        Filtra registros cuya ``accion`` comience con ``COMUNICACION_``
        y los agrupa por ``actor_id`` y ``accion``.

        Args:
            tenant_id: UUID del tenant.
            session: Sesión async.
            scope_actor_id: Filtro opcional por actor.
            desde: Filtro inicio de rango.
            hasta: Filtro fin de rango.

        Returns:
            Lista de dicts ``{"actor_id": UUID, "accion": str, "total": int}``.
        """
        stmt = (
            select(
                self.model.actor_id,  # type: ignore[attr-defined]
                self.model.accion,  # type: ignore[attr-defined]
                func.count().label("total"),
            )
            .where(self.model.tenant_id == tenant_id)  # type: ignore[attr-defined]
            .where(self.model.accion.like("COMUNICACION_%"))  # type: ignore[attr-defined]
            .group_by(self.model.actor_id, self.model.accion)  # type: ignore[attr-defined]
            .order_by(self.model.actor_id, self.model.accion)  # type: ignore[attr-defined]
        )

        if scope_actor_id is not None:
            stmt = stmt.where(self.model.actor_id == scope_actor_id)  # type: ignore[attr-defined]
        if desde is not None:
            stmt = stmt.where(self.model.fecha_hora >= desde)  # type: ignore[attr-defined]
        if hasta is not None:
            stmt = stmt.where(self.model.fecha_hora <= hasta)  # type: ignore[attr-defined]

        result = await session.execute(stmt)
        return [
            {"actor_id": row.actor_id, "accion": row.accion, "total": row.total}
            for row in result
        ]

    async def aggregate_interacciones_docente_materia(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        scope_actor_id: UUID | None = None,
        desde: datetime | None = None,
        hasta: datetime | None = None,
    ) -> list[dict]:
        """Conteo de interacciones por actor, materia y código de acción.

        Agrupa por ``(actor_id, materia_id, accion)``. Incluye ``materia_id``
        nulo como ``None`` (el service decide cómo rotularlo).

        Args:
            tenant_id: UUID del tenant.
            session: Sesión async.
            scope_actor_id: Filtro opcional por actor.
            desde: Filtro inicio de rango.
            hasta: Filtro fin de rango.

        Returns:
            Lista de dicts con ``actor_id``, ``materia_id`` (UUID | None),
            ``accion``, ``total``.
        """
        stmt = (
            select(
                self.model.actor_id,  # type: ignore[attr-defined]
                self.model.materia_id,  # type: ignore[attr-defined]
                self.model.accion,  # type: ignore[attr-defined]
                func.count().label("total"),
            )
            .where(self.model.tenant_id == tenant_id)  # type: ignore[attr-defined]
            .group_by(self.model.actor_id, self.model.materia_id, self.model.accion)  # type: ignore[attr-defined]
            .order_by(self.model.actor_id, self.model.materia_id, self.model.accion)  # type: ignore[attr-defined]
        )

        if scope_actor_id is not None:
            stmt = stmt.where(self.model.actor_id == scope_actor_id)  # type: ignore[attr-defined]
        if desde is not None:
            stmt = stmt.where(self.model.fecha_hora >= desde)  # type: ignore[attr-defined]
        if hasta is not None:
            stmt = stmt.where(self.model.fecha_hora <= hasta)  # type: ignore[attr-defined]

        result = await session.execute(stmt)
        return [
            {
                "actor_id": row.actor_id,
                "materia_id": row.materia_id,
                "accion": row.accion,
                "total": row.total,
            }
            for row in result
        ]
