from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluacion import Evaluacion, ResultadoEvaluacion
from app.models.user import User
from app.repositories.base import BaseRepository


class ResultadoRepository(BaseRepository[ResultadoEvaluacion]):
    def __init__(self) -> None:
        super().__init__(ResultadoEvaluacion)

    async def create_resultado(
        self,
        *,
        tenant_id: UUID,
        evaluacion_id: UUID,
        alumno_id: UUID,
        nota_final: str,
        session: AsyncSession,
    ) -> ResultadoEvaluacion:
        obj = ResultadoEvaluacion(
            tenant_id=tenant_id,
            evaluacion_id=evaluacion_id,
            alumno_id=alumno_id,
            nota_final=nota_final,
        )
        session.add(obj)
        await session.flush()
        await session.refresh(obj)
        return obj

    async def update_nota(
        self,
        *,
        resultado_id: UUID,
        tenant_id: UUID,
        nota_final: str,
        session: AsyncSession,
    ) -> ResultadoEvaluacion | None:
        resultado = await self.get(id=resultado_id, tenant_id=tenant_id, session=session)
        if resultado is None:
            return None
        resultado.nota_final = nota_final
        await session.flush()
        await session.refresh(resultado)
        return resultado

    async def get_by_evaluacion(
        self,
        *,
        evaluacion_id: UUID,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> list[dict]:
        stmt = (
            select(
                ResultadoEvaluacion.id,
                ResultadoEvaluacion.tenant_id,
                ResultadoEvaluacion.evaluacion_id,
                ResultadoEvaluacion.alumno_id,
                ResultadoEvaluacion.nota_final,
                ResultadoEvaluacion.created_at,
                ResultadoEvaluacion.updated_at,
                User.nombre.label("alumno_nombre"),
                User.apellidos.label("alumno_apellidos"),
                User.legajo.label("alumno_legajo"),
            )
            .join(User, ResultadoEvaluacion.alumno_id == User.id)
            .where(
                ResultadoEvaluacion.evaluacion_id == evaluacion_id,
                ResultadoEvaluacion.tenant_id == tenant_id,
                ResultadoEvaluacion.deleted_at.is_(None),
            )
        )
        result = await session.execute(stmt)
        rows = result.all()

        items = []
        for row in rows:
            nombre_completo = None
            if row.alumno_nombre or row.alumno_apellidos:
                nombre_completo = f"{row.alumno_nombre or ''} {row.alumno_apellidos or ''}".strip()
            items.append({
                "id": row.id,
                "tenant_id": row.tenant_id,
                "evaluacion_id": row.evaluacion_id,
                "alumno_id": row.alumno_id,
                "nota_final": row.nota_final,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
                "alumno_nombre": nombre_completo,
                "alumno_legajo": row.alumno_legajo,
            })
        return items

    async def get_registro_academico(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        materia_id: Optional[UUID] = None,
        cohorte_id: Optional[UUID] = None,
        alumno_id: Optional[UUID] = None,
    ) -> list[dict]:
        conditions = [
            ResultadoEvaluacion.tenant_id == tenant_id,
            ResultadoEvaluacion.deleted_at.is_(None),
            Evaluacion.tenant_id == tenant_id,
            Evaluacion.deleted_at.is_(None),
            User.tenant_id == tenant_id,
            User.deleted_at.is_(None),
        ]

        if materia_id is not None:
            conditions.append(Evaluacion.materia_id == materia_id)
        if cohorte_id is not None:
            conditions.append(Evaluacion.cohorte_id == cohorte_id)
        if alumno_id is not None:
            conditions.append(ResultadoEvaluacion.alumno_id == alumno_id)

        stmt = (
            select(
                ResultadoEvaluacion.id.label("resultado_id"),
                ResultadoEvaluacion.evaluacion_id,
                ResultadoEvaluacion.alumno_id,
                ResultadoEvaluacion.nota_final,
                ResultadoEvaluacion.created_at,
                Evaluacion.materia_id,
                Evaluacion.cohorte_id,
                Evaluacion.instancia,
                Evaluacion.tipo,
                User.nombre.label("alumno_nombre"),
                User.apellidos.label("alumno_apellidos"),
                User.legajo.label("alumno_legajo"),
            )
            .join(Evaluacion, ResultadoEvaluacion.evaluacion_id == Evaluacion.id)
            .join(User, ResultadoEvaluacion.alumno_id == User.id)
            .where(*conditions)
            .order_by(ResultadoEvaluacion.created_at.desc())
        )
        result = await session.execute(stmt)
        rows = result.all()

        items = []
        for row in rows:
            nombre_completo = None
            if row.alumno_nombre or row.alumno_apellidos:
                nombre_completo = f"{row.alumno_nombre or ''} {row.alumno_apellidos or ''}".strip()
            items.append({
                "resultado_id": row.resultado_id,
                "evaluacion_id": row.evaluacion_id,
                "materia_id": row.materia_id,
                "materia_nombre": None,
                "cohorte_id": row.cohorte_id,
                "instancia": row.instancia,
                "tipo": row.tipo,
                "alumno_id": row.alumno_id,
                "alumno_nombre": nombre_completo,
                "alumno_legajo": row.alumno_legajo,
                "nota_final": row.nota_final,
                "created_at": row.created_at,
            })
        return items
