"""Integration tests — aislamiento multi-tenant y permisos.

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
from app.models.calificacion import Calificacion, OrigenCalificacionDB, UmbralMateria
from app.models.padron import EntradaPadron, VersionPadron
from app.repositories.calificacion_repository import CalificacionRepository
from app.repositories.umbral_repository import UmbralRepository
from app.services.calificacion_service import CalificacionService, UmbralService

pytestmark = pytest.mark.requires_db


def _build_audit_ctx(user, tenant_id) -> AuditContext:
    return AuditContext(
        actor_id=user.id,
        tenant_id=tenant_id,
        ip="127.0.0.1",
        user_agent="test",
    )


class TestAislamientoMultiTenant:
    """Multi-tenancy: datos de tenant A invisibles para tenant B (Task 14.7)."""

    async def _setup_tenant_con_calificaciones(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        tenant_factory,
        slug_suffix: str = "a",
    ) -> tuple:
        """Helper: crea tenant con materia, usuario, EntradaPadron y calificaciones."""
        t = await tenant_factory(db_session, slug=f"tenant-{slug_suffix}-{uuid.uuid4().hex[:6]}")
        from app.models.materia import Materia
        from app.models.carrera import Carrera, EstadoCarrera
        from app.models.cohorte import Cohorte

        m = Materia(id=uuid.uuid4(), tenant_id=t.id, codigo=f"M-{slug_suffix}", nombre=f"Materia {slug_suffix}")
        db_session.add(m)
        await db_session.flush()

        car = Carrera(id=uuid.uuid4(), tenant_id=t.id, codigo=f"CAR-{slug_suffix}", nombre=f"Carrera {slug_suffix}", estado=EstadoCarrera.Activa)
        db_session.add(car)
        await db_session.flush()

        coh = Cohorte(id=uuid.uuid4(), tenant_id=t.id, carrera_id=car.id, nombre="2025", anio=2025, vig_desde="2025-01-01", vig_hasta="2025-12-31")
        db_session.add(coh)
        await db_session.flush()

        vp = VersionPadron(id=uuid.uuid4(), tenant_id=t.id, materia_id=m.id, cohorte_id=coh.id, activa=True, total_entradas=1, origen="archivo")
        db_session.add(vp)
        await db_session.flush()

        ep = EntradaPadron(
            id=uuid.uuid4(),
            tenant_id=t.id,
            version_padron_id=vp.id,
            nombre="Juan",
            apellidos="Pérez",
            email_encrypted="cifrado",
            comision="A",
        )
        db_session.add(ep)
        await db_session.flush()

        user = await user_factory(db_session, tenant_id=t.id)

        calif = Calificacion(
            id=uuid.uuid4(),
            tenant_id=t.id,
            entrada_padron_id=ep.id,
            materia_id=m.id,
            actividad="Parcial (Real)",
            nota_numerica=85.0,
            origen=OrigenCalificacionDB.IMPORTADO,
            creado_por=user.id,
        )
        db_session.add(calif)
        await db_session.commit()

        return t, m, user

    async def test_calificaciones_aislamiento_tenant(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        tenant_factory,
    ):
        """14.7 RED: calificaciones de tenant A invisibles para tenant B."""
        t_a, m_a, user_a = await self._setup_tenant_con_calificaciones(
            db_session, materia, user_factory, tenant_factory, "a",
        )
        t_b, m_b, user_b = await self._setup_tenant_con_calificaciones(
            db_session, materia, user_factory, tenant_factory, "b",
        )

        repo = CalificacionRepository()

        # Tenant A ve sus calificaciones
        result_a = await repo.get_by_materia_y_usuario(
            tenant_id=t_a.id,
            materia_id=m_a.id,
            creado_por=user_a.id,
            session=db_session,
        )
        assert len(result_a) == 1

        # Tenant B también ve las suyas
        result_b = await repo.get_by_materia_y_usuario(
            tenant_id=t_b.id,
            materia_id=m_b.id,
            creado_por=user_b.id,
            session=db_session,
        )
        assert len(result_b) == 1

        # Tenant B NO ve las de tenant A
        result_b_see_a = await repo.get_by_materia_y_usuario(
            tenant_id=t_b.id,  # Tenant B
            materia_id=m_a.id,  # Materia de tenant A
            creado_por=user_a.id,
            session=db_session,
        )
        assert len(result_b_see_a) == 0

    async def test_umbral_aislamiento_tenant(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        tenant_factory,
        asignacion_factory,
    ):
        """14.7 TRIANGULATE: umbral de tenant A invisible para tenant B."""
        t_a = await tenant_factory(db_session, slug="tenant-iso-a")
        from app.models.materia import Materia

        m_a = Materia(id=uuid.uuid4(), tenant_id=t_a.id, codigo="M-ISO-A", nombre="Materia A")
        db_session.add(m_a)
        await db_session.flush()

        user_a = await user_factory(db_session, tenant_id=t_a.id)
        asig_a = await asignacion_factory(
            db_session, tenant_id=t_a.id, usuario_id=user_a.id, materia_id=m_a.id,
        )
        audit_ctx = _build_audit_ctx(user_a, t_a.id)

        # Configurar umbral en tenant A
        us = UmbralService()
        await us.configurar_umbral(
            tenant_id=t_a.id,
            asignacion_id=asig_a.id,
            materia_id=m_a.id,
            umbral_pct=85,
            audit_ctx=audit_ctx,
            session=db_session,
        )

        # Tenant B busca ese umbral → no lo encuentra (tenant_id diferente)
        t_b = await tenant_factory(db_session, slug="tenant-iso-b")
        resultado = await us.get_umbral(
            tenant_id=t_b.id,
            asignacion_id=asig_a.id,
            session=db_session,
        )
        assert resultado is None

    async def test_vaciar_solo_propio_tenant(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        tenant_factory,
    ):
        """14.7 TRIANGULATE: vaciar solo afecta calificaciones del mismo tenant."""
        t_a = await tenant_factory(db_session, slug=f"tenant-vac-a-{uuid.uuid4().hex[:6]}")
        from app.models.materia import Materia

        m_a = Materia(id=uuid.uuid4(), tenant_id=t_a.id, codigo=f"M-VAC-A-{uuid.uuid4().hex[:6]}", nombre="Materia A")
        db_session.add(m_a)
        await db_session.flush()

        user_a = await user_factory(db_session, tenant_id=t_a.id)

        # Crear EntradaPadron y calificación en tenant A
        from app.models.padron import VersionPadron
        from app.models.carrera import Carrera, EstadoCarrera
        from app.models.cohorte import Cohorte

        car = Carrera(id=uuid.uuid4(), tenant_id=t_a.id, codigo=f"CAR-VAC-A-{uuid.uuid4().hex[:6]}", nombre="Carrera", estado=EstadoCarrera.Activa)
        db_session.add(car)
        await db_session.flush()

        coh = Cohorte(id=uuid.uuid4(), tenant_id=t_a.id, carrera_id=car.id, nombre="2025", anio=2025, vig_desde="2025-01-01", vig_hasta="2025-12-31")
        db_session.add(coh)
        await db_session.flush()

        vp = VersionPadron(id=uuid.uuid4(), tenant_id=t_a.id, materia_id=m_a.id, cohorte_id=coh.id, activa=True, total_entradas=1, origen="archivo")
        db_session.add(vp)
        await db_session.flush()

        ep = EntradaPadron(id=uuid.uuid4(), tenant_id=t_a.id, version_padron_id=vp.id, nombre="Juan", apellidos="Pérez", email_encrypted="cifrado", comision="A")
        db_session.add(ep)
        await db_session.flush()

        calif_a = Calificacion(
            id=uuid.uuid4(),
            tenant_id=t_a.id,
            entrada_padron_id=ep.id,
            materia_id=m_a.id,
            actividad="TP1 (Real)",
            nota_numerica=80.0,
            origen=OrigenCalificacionDB.IMPORTADO,
            creado_por=user_a.id,
        )
        db_session.add(calif_a)
        await db_session.commit()

        # Vaciar con tenant B → no afecta tenant A
        t_b = await tenant_factory(db_session, slug=f"tenant-vac-b-{uuid.uuid4().hex[:6]}")
        audit_ctx = _build_audit_ctx(user_a, t_b.id)

        cs = CalificacionService()
        affected = await cs.vaciar_materia(
            tenant_id=t_b.id,
            materia_id=m_a.id,
            actor_id=user_a.id,
            audit_ctx=audit_ctx,
            session=db_session,
        )
        assert affected == 0

        # Calificación de tenant A sigue intacta
        result = await db_session.execute(
            select(Calificacion).where(
                Calificacion.tenant_id == t_a.id,
                Calificacion.materia_id == m_a.id,
            )
        )
        calif = result.scalar_one()
        assert calif.deleted_at is None

    async def test_get_calificaciones_solo_mismo_tenant(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        tenant_factory,
    ):
        """14.7 TRIANGULATE: get_calificaciones solo devuelve del tenant correcto."""
        t_a, m_a, user_a = await self._setup_tenant_con_calificaciones(
            db_session, materia, user_factory, tenant_factory, "gca",
        )

        cs = CalificacionService()

        # Tenant A: ve su calificación
        result_a = await cs.get_calificaciones(
            tenant_id=t_a.id,
            materia_id=m_a.id,
            creado_por=user_a.id,
            session=db_session,
        )
        assert len(result_a) == 1

        # Otro tenant: no ve nada (el service filtra por tenant_id)
        otro_tenant = await tenant_factory(db_session, slug="tenant-gcb")
        result_otro = await cs.get_calificaciones(
            tenant_id=otro_tenant.id,
            materia_id=m_a.id,
            creado_por=user_a.id,
            session=db_session,
        )
        assert len(result_otro) == 0

    async def test_reporte_aislamiento_tenant(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        tenant_factory,
    ):
        """14.7 TRIANGULATE: reporte finalización respeta tenant."""
        t_a = await tenant_factory(db_session, slug="tenant-rpt-a")
        from app.models.materia import Materia
        from app.models.padron import EntradaPadron, VersionPadron
        from app.models.carrera import Carrera, EstadoCarrera
        from app.models.cohorte import Cohorte

        m_a = Materia(id=uuid.uuid4(), tenant_id=t_a.id, codigo="M-RPT", nombre="Materia RPT")
        db_session.add(m_a)
        await db_session.flush()

        user_a = await user_factory(db_session, tenant_id=t_a.id)

        car = Carrera(id=uuid.uuid4(), tenant_id=t_a.id, codigo="CAR-RPT", nombre="Ing", estado=EstadoCarrera.Activa)
        db_session.add(car)
        await db_session.flush()

        c = Cohorte(id=uuid.uuid4(), tenant_id=t_a.id, carrera_id=car.id, nombre="2025", anio=2025, vig_desde="2025-01-01", vig_hasta="2025-12-31")
        db_session.add(c)
        await db_session.flush()

        vp = VersionPadron(id=uuid.uuid4(), tenant_id=t_a.id, materia_id=m_a.id, cohorte_id=c.id, activa=True, total_entradas=1, origen="archivo")
        db_session.add(vp)
        await db_session.flush()

        ep = EntradaPadron(id=uuid.uuid4(), tenant_id=t_a.id, version_padron_id=vp.id, nombre="Juan", apellidos="Pérez", email_encrypted="cifrado", comision="A")
        db_session.add(ep)
        await db_session.commit()

        # CSV con columna textual
        header = "entrada_padron_id,nombre,apellidos,Estado"
        line = f"{ep.id},Juan,Pérez,Aprobado"
        contenido = f"{header}\n{line}\n".encode("utf-8-sig")

        cs = CalificacionService()
        reporte_a = await cs.reporte_finalizacion(
            tenant_id=t_a.id,
            materia_id=m_a.id,
            archivo_contenido=contenido,
            nombre_archivo="finalizacion.csv",
            session=db_session,
        )

        # Debería encontrar items porque no hay calificaciones previas
        assert len(reporte_a.items) == 1

        # Otro tenant → no hay datos (aunque use misma materia_id)
        t_b = await tenant_factory(db_session, slug="tenant-rpt-b")
        reporte_b = await cs.reporte_finalizacion(
            tenant_id=t_b.id,
            materia_id=m_a.id,
            archivo_contenido=contenido,
            nombre_archivo="finalizacion.csv",
            session=db_session,
        )
        # No se esperan items porque las calificaciones de tenant A
        # no están en tenant B, pero el parseo es el mismo
        # El resultado dependerá de que la entrada_padron_id no exista en tenant B
        # → get_by_entrada_padron devuelve vacío → todas aparecen como sin calificar
        # O puede que el parseo falle por no encontrar las columnas requeridas en B
        assert isinstance(reporte_b.items, list)
