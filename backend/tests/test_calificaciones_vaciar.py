"""Integration tests — vaciado de calificaciones (RN-04, F1.5).

Strict TDD: RED → GREEN → TRIANGULATE → REFACTOR.
Usa contenedor de DB efímero — no mocks.
Marcado @pytest.mark.requires_db.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditContext
from app.models.calificacion import Calificacion, OrigenCalificacionDB
from app.models.padron import EntradaPadron
from app.services.calificacion_service import CalificacionService

pytestmark = pytest.mark.requires_db


def _build_audit_ctx(user, tenant_id) -> AuditContext:
    return AuditContext(
        actor_id=user.id,
        tenant_id=tenant_id,
        ip="127.0.0.1",
        user_agent="test",
    )


class TestVaciarCalificaciones:
    """Vaciar calificaciones scoped al usuario (Task 14.6)."""

    async def _crear_calificaciones(
        self,
        db_session: AsyncSession,
        tenant_id,
        materia_id,
        user_id,
        cantidad: int = 3,
    ) -> list[Calificacion]:
        """Helper: crear N calificaciones para un usuario con EntradaPadron."""
        from app.models.padron import VersionPadron
        from app.models.cohorte import Cohorte
        from app.models.carrera import Carrera, EstadoCarrera

        car = Carrera(id=uuid.uuid4(), tenant_id=tenant_id, codigo=f"CAR-{uuid.uuid4().hex[:8]}", nombre="Carrera", estado=EstadoCarrera.Activa)
        db_session.add(car)
        await db_session.flush()

        c = Cohorte(id=uuid.uuid4(), tenant_id=tenant_id, carrera_id=car.id, nombre="2025", anio=2025, vig_desde="2025-01-01", vig_hasta="2025-12-31")
        db_session.add(c)
        await db_session.flush()

        vp = VersionPadron(id=uuid.uuid4(), tenant_id=tenant_id, materia_id=materia_id, cohorte_id=c.id, activa=True, total_entradas=cantidad, origen="archivo")
        db_session.add(vp)
        await db_session.flush()

        califs = []
        for i in range(cantidad):
            ep = EntradaPadron(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                version_padron_id=vp.id,
                nombre=f"Alumno{i+1}",
                apellidos="Test",
                email_encrypted="cifrado",
                comision="A",
            )
            db_session.add(ep)
            await db_session.flush()

            c = Calificacion(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                entrada_padron_id=ep.id,
                materia_id=materia_id,
                actividad=f"TP{i+1} (Real)",
                nota_numerica=float(70 + i),
                origen=OrigenCalificacionDB.IMPORTADO,
                creado_por=user_id,
            )
            db_session.add(c)
            califs.append(c)
        await db_session.commit()
        for c in califs:
            await db_session.refresh(c)
        return califs

    async def test_vaciar_calificaciones_propias(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
    ):
        """14.6 RED: vaciar soft-deletea calificaciones del usuario."""
        t, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        audit_ctx = _build_audit_ctx(user, t.id)

        await self._crear_calificaciones(db_session, t.id, m.id, user.id)

        service = CalificacionService()
        affected = await service.vaciar_materia(
            tenant_id=t.id,
            materia_id=m.id,
            actor_id=user.id,
            audit_ctx=audit_ctx,
            session=db_session,
        )
        assert affected == 3

        # Verificar soft-delete
        stmt = (
            select(Calificacion)
            .where(
                Calificacion.tenant_id == t.id,
                Calificacion.materia_id == m.id,
                Calificacion.creado_por == user.id,
            )
        )
        result = await db_session.execute(stmt)
        califs = result.scalars().all()
        assert len(califs) == 3
        for c in califs:
            assert c.deleted_at is not None
            assert c.deleted_by == user.id

    async def test_vaciar_no_afecta_otro_docente(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
    ):
        """14.6 RED: vaciar solo borra calificaciones del actor, no de otros."""
        t, m = materia
        user_a = await user_factory(db_session, tenant_id=t.id, email="docente_a@e.com")
        user_b = await user_factory(db_session, tenant_id=t.id, email="docente_b@e.com")
        audit_ctx = _build_audit_ctx(user_a, t.id)

        # Ambos crean calificaciones
        await self._crear_calificaciones(db_session, t.id, m.id, user_a.id, cantidad=2)
        await self._crear_calificaciones(db_session, t.id, m.id, user_b.id, cantidad=2)

        service = CalificacionService()
        affected = await service.vaciar_materia(
            tenant_id=t.id,
            materia_id=m.id,
            actor_id=user_a.id,
            audit_ctx=audit_ctx,
            session=db_session,
        )
        assert affected == 2

        # user_a soft-deleteado
        stmt_a = (
            select(Calificacion)
            .where(
                Calificacion.tenant_id == t.id,
                Calificacion.creado_por == user_a.id,
            )
        )
        result_a = await db_session.execute(stmt_a)
        for c in result_a.scalars().all():
            assert c.deleted_at is not None

        # user_b intacto
        stmt_b = (
            select(Calificacion)
            .where(
                Calificacion.tenant_id == t.id,
                Calificacion.creado_por == user_b.id,
            )
        )
        result_b = await db_session.execute(stmt_b)
        for c in result_b.scalars().all():
            assert c.deleted_at is None

    async def test_vaciar_sin_calificaciones_204(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
    ):
        """14.6 TRIANGULATE: vaciar sin calificaciones → 0 afectados."""
        t, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        audit_ctx = _build_audit_ctx(user, t.id)

        service = CalificacionService()
        affected = await service.vaciar_materia(
            tenant_id=t.id,
            materia_id=m.id,
            actor_id=user.id,
            audit_ctx=audit_ctx,
            session=db_session,
        )
        assert affected == 0

    async def test_doble_vaciado_204(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
    ):
        """14.6 TRIANGULATE: doble vaciado → 0 afectados segunda vez."""
        t, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        audit_ctx = _build_audit_ctx(user, t.id)

        await self._crear_calificaciones(db_session, t.id, m.id, user.id, cantidad=1)

        service = CalificacionService()

        # Primer vaciado
        affected1 = await service.vaciar_materia(
            tenant_id=t.id,
            materia_id=m.id,
            actor_id=user.id,
            audit_ctx=audit_ctx,
            session=db_session,
        )
        assert affected1 == 1

        # Segundo vaciado (ya vaciado)
        affected2 = await service.vaciar_materia(
            tenant_id=t.id,
            materia_id=m.id,
            actor_id=user.id,
            audit_ctx=audit_ctx,
            session=db_session,
        )
        assert affected2 == 0

    async def test_vaciar_materia_otro_tenant_404(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        tenant_factory,
    ):
        """14.6 TRIANGULATE: vaciar materia de otro tenant → 0 (scoped por tenant)."""
        t1, m1 = materia
        user1 = await user_factory(db_session, tenant_id=t1.id)
        audit_ctx = _build_audit_ctx(user1, t1.id)

        await self._crear_calificaciones(db_session, t1.id, m1.id, user1.id, cantidad=1)

        # Vaciar con tenant diferente al de las calificaciones
        t2 = await tenant_factory(db_session, slug="otro-tenant")

        service = CalificacionService()
        affected = await service.vaciar_materia(
            tenant_id=t2.id,  # Tenant B
            materia_id=m1.id,  # Materia de tenant A
            actor_id=user1.id,
            audit_ctx=audit_ctx,
            session=db_session,
        )
        assert affected == 0  # No hay calificaciones de tenant B

        # Las de tenant A siguen intactas
        stmt = (
            select(Calificacion)
            .where(
                Calificacion.tenant_id == t1.id,
                Calificacion.materia_id == m1.id,
            )
        )
        result = await db_session.execute(stmt)
        califs = result.scalars().all()
        assert len(califs) == 1
        assert califs[0].deleted_at is None  # No afectadas
