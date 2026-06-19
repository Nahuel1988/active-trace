"""AsignacionRepository — operaciones de acceso a datos para el modelo Asignacion.

Responsabilidades:
    - CRUD con filtro SIEMPRE por tenant_id.
    - Soft delete (deleted_at). Nunca hard delete.
    - Filtro por estado_vigencia ('vigente', 'vencida', 'todas').
    - list_vigentes_for_user: permisos efectivos.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asignacion import Asignacion
from app.repositories.base import BaseRepository


def _vigentes_clause(now: datetime):
    """Cláusula WHERE de vigencia reutilizable para Asignacion.

    Vigente: desde <= now AND (hasta IS NULL OR hasta >= now)
             AND deleted_at IS NULL
    """
    return and_(
        Asignacion.desde <= now,
        or_(Asignacion.hasta.is_(None), Asignacion.hasta >= now),
        Asignacion.deleted_at.is_(None),
    )


class AsignacionRepository(BaseRepository[Asignacion]):
    """Repositorio para el modelo Asignacion con tenant-scoping y filtro de vigencia."""

    def __init__(self) -> None:
        super().__init__(Asignacion)

    async def create(
        self,
        *,
        tenant_id: UUID,
        usuario_id: UUID,
        role_id: UUID,
        desde: datetime,
        hasta: Optional[datetime] = None,
        materia_id: Optional[UUID] = None,
        carrera_id: Optional[UUID] = None,
        cohorte_id: Optional[UUID] = None,
        responsable_id: Optional[UUID] = None,
        comisiones: Optional[List[str]] = None,
        session: AsyncSession,
    ) -> Asignacion:
        """Crea una nueva asignación.

        Args:
            tenant_id: UUID del tenant (derivado del JWT del caller).
            usuario_id: UUID del usuario asignado.
            role_id: UUID del rol.
            desde: Fecha de inicio de vigencia.
            hasta: Fecha de fin de vigencia (None = indefinida).
            materia_id: UUID de materia (nullable).
            carrera_id: UUID de carrera (nullable).
            cohorte_id: UUID de cohorte (nullable).
            responsable_id: UUID del responsable jerárquico (nullable).
            comisiones: Lista de comisiones (default vacío).
            session: Sesión async.

        Returns:
            Asignacion creada con id y timestamps.
        """
        asig = Asignacion(
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            role_id=role_id,
            desde=desde,
            hasta=hasta,
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
            responsable_id=responsable_id,
            comisiones=comisiones or [],
        )
        session.add(asig)
        await session.flush()
        await session.refresh(asig)
        return asig

    async def list(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        estado_vigencia: str = "vigente",
        usuario_id: Optional[UUID] = None,
        materia_id: Optional[UUID] = None,
        carrera_id: Optional[UUID] = None,
        cohorte_id: Optional[UUID] = None,
        role_id: Optional[UUID] = None,
        responsable_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Asignacion]:
        """Lista asignaciones con filtros y control de vigencia.

        Args:
            tenant_id: UUID del tenant (obligatorio).
            session: Sesión async.
            estado_vigencia: 'vigente' (default) | 'vencida' | 'todas'.
            usuario_id: Filtrar por usuario (opcional).
            materia_id: Filtrar por materia (opcional).
            carrera_id: Filtrar por carrera (opcional).
            cohorte_id: Filtrar por cohorte (opcional).
            role_id: Filtrar por rol (opcional).
            responsable_id: Filtrar por responsable (opcional).
            limit: Máximo de registros (default 50).
            offset: Desplazamiento para paginación.

        Returns:
            Lista de Asignacion según los filtros aplicados.
        """
        now = datetime.now(timezone.utc)

        # Base: siempre filtrar por tenant y excluir soft-deleted
        conditions = [
            Asignacion.tenant_id == tenant_id,
            Asignacion.deleted_at.is_(None),
        ]

        # Aplicar filtro de vigencia
        if estado_vigencia == "vigente":
            conditions.extend([
                Asignacion.desde <= now,
                or_(Asignacion.hasta.is_(None), Asignacion.hasta >= now),
            ])
        elif estado_vigencia == "vencida":
            conditions.append(
                or_(
                    Asignacion.desde > now,
                    and_(Asignacion.hasta.is_not(None), Asignacion.hasta < now),
                )
            )
        # "todas": solo excluir soft-deleted (ya está en base)

        # Filtros opcionales de contexto
        if usuario_id is not None:
            conditions.append(Asignacion.usuario_id == usuario_id)
        if materia_id is not None:
            conditions.append(Asignacion.materia_id == materia_id)
        if carrera_id is not None:
            conditions.append(Asignacion.carrera_id == carrera_id)
        if cohorte_id is not None:
            conditions.append(Asignacion.cohorte_id == cohorte_id)
        if role_id is not None:
            conditions.append(Asignacion.role_id == role_id)
        if responsable_id is not None:
            conditions.append(Asignacion.responsable_id == responsable_id)

        stmt = (
            select(Asignacion)
            .where(*conditions)
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def list_vigentes_for_user(
        self,
        *,
        user_id: UUID,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> List[Asignacion]:
        """Retorna asignaciones vigentes para resolver permisos efectivos.

        Usado por PermisoRepository al calcular permisos efectivos (D5).

        Args:
            user_id: UUID del usuario.
            tenant_id: UUID del tenant.
            session: Sesión async.

        Returns:
            Lista de Asignacion vigentes y no soft-deleted del usuario.
        """
        now = datetime.now(timezone.utc)
        stmt = select(Asignacion).where(
            Asignacion.user_id == user_id,  # type: ignore[attr-defined]
            Asignacion.tenant_id == tenant_id,
            _vigentes_clause(now),
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
