from __future__ import annotations

import uuid as _uuid
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.evaluacion import Evaluacion, ReservaEvaluacion, ResultadoEvaluacion
from app.models.user import User
from app.repositories.base import BaseRepository


class EvaluacionRepository(BaseRepository[Evaluacion]):
    def __init__(self) -> None:
        super().__init__(Evaluacion)

    async def create_evaluacion(
        self,
        *,
        tenant_id: UUID,
        materia_id: UUID,
        cohorte_id: UUID,
        tipo: str,
        instancia: str,
        dias_disponibles: int,
        session: AsyncSession,
    ) -> Evaluacion:
        obj = Evaluacion(
            tenant_id=tenant_id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            tipo=tipo,
            instancia=instancia,
            dias_disponibles=dias_disponibles,
        )
        session.add(obj)
        await session.flush()
        await session.refresh(obj)
        return obj

    async def update_evaluacion(
        self,
        *,
        id: UUID,
        tenant_id: UUID,
        data: dict[str, Any],
        session: AsyncSession,
    ) -> Evaluacion | None:
        evaluacion = await self.get(id=id, tenant_id=tenant_id, session=session)
        if evaluacion is None:
            return None
        for field, value in data.items():
            if hasattr(evaluacion, field):
                setattr(evaluacion, field, value)
        await session.flush()
        await session.refresh(evaluacion)
        return evaluacion

    async def import_candidatos(
        self,
        *,
        tenant_id: UUID,
        evaluacion_id: UUID,
        usuario_ids: list[UUID],
        session: AsyncSession,
    ) -> tuple[list[UUID], list[dict]]:
        evaluacion = await self.get(id=evaluacion_id, tenant_id=tenant_id, session=session)
        if evaluacion is None:
            return [], []

        existing = set(evaluacion.candidatos or [])
        existing_str = {str(uid) for uid in existing}
        registrados: list[UUID] = []
        rechazados: list[dict] = []

        for uid in usuario_ids:
            if str(uid) in existing_str:
                rechazados.append({"usuario_id": str(uid), "motivo": "El usuario ya está registrado como candidato"})
                continue
            user = await session.get(User, uid)
            if user is None or user.tenant_id != tenant_id or user.deleted_at is not None:
                rechazados.append({"usuario_id": str(uid), "motivo": "El usuario no pertenece al tenant"})
                continue
            from app.models.role import Role, UserRole
            stmt = (
                select(UserRole)
                .join(Role, UserRole.role_id == Role.id)
                .where(
                    UserRole.user_id == uid,
                    UserRole.tenant_id == tenant_id,
                    Role.code == "alumno",
                    UserRole.hasta.is_(None),
                )
            )
            result = await session.execute(stmt)
            user_role = result.scalar_one_or_none()
            if user_role is None:
                rechazados.append({"usuario_id": str(uid), "motivo": "El usuario no tiene rol ALUMNO"})
                continue
            registrados.append(uid)

        if registrados:
            nuevos = list(existing)
            for uid in registrados:
                nuevos.append(str(uid))
            stmt = (
                update(Evaluacion)
                .where(Evaluacion.id == evaluacion_id, Evaluacion.tenant_id == tenant_id)
                .values(candidatos=nuevos)
            )
            await session.execute(stmt)
            await session.flush()

        return registrados, rechazados

    async def list_with_metrics(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        base_conditions = [
            Evaluacion.tenant_id == tenant_id,
            Evaluacion.deleted_at.is_(None),
        ]

        stmt = (
            select(
                Evaluacion.id,
                Evaluacion.tenant_id,
                Evaluacion.materia_id,
                Evaluacion.cohorte_id,
                Evaluacion.tipo,
                Evaluacion.instancia,
                Evaluacion.dias_disponibles,
                Evaluacion.candidatos,
                Evaluacion.created_at,
                Evaluacion.updated_at,
            )
            .where(*base_conditions)
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(stmt)
        rows = result.all()

        items = []
        for row in rows:
            convocados = len(row.candidatos or [])
            res_activas = await self._count_reservas_activas(
                evaluacion_id=row.id, tenant_id=tenant_id, session=session
            )
            items.append({
                "id": row.id,
                "tenant_id": row.tenant_id,
                "materia_id": row.materia_id,
                "cohorte_id": row.cohorte_id,
                "tipo": row.tipo,
                "instancia": row.instancia,
                "dias_disponibles": row.dias_disponibles,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
                "convocados": convocados,
                "reservas_activas": res_activas,
                "cupos_libres": max(0, row.dias_disponibles - res_activas),
            })
        return items

    async def get_with_metrics(
        self,
        *,
        id: UUID,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> dict | None:
        evaluacion = await self.get(id=id, tenant_id=tenant_id, session=session)
        if evaluacion is None:
            return None
        convocados = len(evaluacion.candidatos or [])
        res_activas = await self._count_reservas_activas(
            evaluacion_id=id, tenant_id=tenant_id, session=session
        )
        return {
            "id": evaluacion.id,
            "tenant_id": evaluacion.tenant_id,
            "materia_id": evaluacion.materia_id,
            "cohorte_id": evaluacion.cohorte_id,
            "tipo": evaluacion.tipo,
            "instancia": evaluacion.instancia,
            "dias_disponibles": evaluacion.dias_disponibles,
            "created_at": evaluacion.created_at,
            "updated_at": evaluacion.updated_at,
            "convocados": convocados,
            "reservas_activas": res_activas,
            "cupos_libres": max(0, evaluacion.dias_disponibles - res_activas),
        }

    async def get_metricas_panel(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> dict:
        base = and_(Evaluacion.tenant_id == tenant_id, Evaluacion.deleted_at.is_(None))

        instancias = await session.execute(
            select(func.count(Evaluacion.id)).where(base)
        )
        instancias_activas = instancias.scalar() or 0

        candidatos_sub = select(func.count(func.jsonb_array_elements(Evaluacion.candidatos))).where(base)
        total_candidatos_row = await session.execute(
            select(func.coalesce(func.sum(func.jsonb_array_length(Evaluacion.candidatos)), 0)).where(base)
        )
        total_candidatos = total_candidatos_row.scalar() or 0

        reservas = await session.execute(
            select(func.count(ReservaEvaluacion.id)).where(
                ReservaEvaluacion.tenant_id == tenant_id,
                ReservaEvaluacion.estado == "Activa",
                ReservaEvaluacion.deleted_at.is_(None),
            )
        )
        reservas_activas = reservas.scalar() or 0

        notas = await session.execute(
            select(func.count(ResultadoEvaluacion.id)).where(
                ResultadoEvaluacion.tenant_id == tenant_id,
                ResultadoEvaluacion.deleted_at.is_(None),
            )
        )
        notas_registradas = notas.scalar() or 0

        return {
            "total_candidatos": total_candidatos,
            "instancias_activas": instancias_activas,
            "reservas_activas": reservas_activas,
            "notas_registradas": notas_registradas,
        }

    async def get_agenda(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        materia_id: Optional[UUID] = None,
        cohorte_id: Optional[UUID] = None,
        evaluacion_id: Optional[UUID] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
    ) -> list[dict]:
        conditions = [
            ReservaEvaluacion.tenant_id == tenant_id,
            ReservaEvaluacion.estado == "Activa",
            ReservaEvaluacion.deleted_at.is_(None),
            Evaluacion.tenant_id == tenant_id,
            Evaluacion.deleted_at.is_(None),
        ]

        if materia_id is not None:
            conditions.append(Evaluacion.materia_id == materia_id)
        if cohorte_id is not None:
            conditions.append(Evaluacion.cohorte_id == cohorte_id)
        if evaluacion_id is not None:
            conditions.append(ReservaEvaluacion.evaluacion_id == evaluacion_id)
        if fecha_desde is not None:
            conditions.append(ReservaEvaluacion.fecha_hora >= fecha_desde)
        if fecha_hasta is not None:
            conditions.append(ReservaEvaluacion.fecha_hora <= fecha_hasta)

        stmt = (
            select(
                ReservaEvaluacion.id.label("reserva_id"),
                ReservaEvaluacion.evaluacion_id,
                ReservaEvaluacion.alumno_id,
                ReservaEvaluacion.fecha_hora,
                ReservaEvaluacion.estado,
                Evaluacion.materia_id,
                Evaluacion.cohorte_id,
                Evaluacion.instancia,
                Evaluacion.tipo,
                User.nombre.label("alumno_nombre"),
                User.apellidos.label("alumno_apellidos"),
                User.legajo.label("alumno_legajo"),
            )
            .join(Evaluacion, ReservaEvaluacion.evaluacion_id == Evaluacion.id)
            .join(User, ReservaEvaluacion.alumno_id == User.id)
            .where(*conditions)
            .order_by(ReservaEvaluacion.fecha_hora)
        )
        result = await session.execute(stmt)
        rows = result.all()

        items = []
        for row in rows:
            nombre_completo = None
            if row.alumno_nombre or row.alumno_apellidos:
                nombre_completo = f"{row.alumno_nombre or ''} {row.alumno_apellidos or ''}".strip()
            items.append({
                "reserva_id": row.reserva_id,
                "evaluacion_id": row.evaluacion_id,
                "materia_id": row.materia_id,
                "materia_nombre": None,
                "cohorte_id": row.cohorte_id,
                "instancia": row.instancia,
                "tipo": row.tipo,
                "alumno_id": row.alumno_id,
                "alumno_nombre": nombre_completo,
                "alumno_legajo": row.alumno_legajo,
                "fecha_hora": row.fecha_hora,
                "estado": row.estado,
            })
        return items

    async def _count_reservas_activas(
        self,
        *,
        evaluacion_id: UUID,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> int:
        stmt = select(func.count(ReservaEvaluacion.id)).where(
            ReservaEvaluacion.evaluacion_id == evaluacion_id,
            ReservaEvaluacion.tenant_id == tenant_id,
            ReservaEvaluacion.estado == "Activa",
            ReservaEvaluacion.deleted_at.is_(None),
        )
        result = await session.execute(stmt)
        return result.scalar() or 0
