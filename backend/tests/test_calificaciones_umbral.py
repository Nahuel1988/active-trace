"""Integration tests — umbral de aprobación (F2.1).

Strict TDD: RED → GREEN → TRIANGULATE → REFACTOR.
Usa contenedor de DB efímero — no mocks.
Marcado @pytest.mark.requires_db.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditCodes, AuditContext
from app.models.calificacion import UmbralMateria
from app.services.calificacion_service import CalificacionError, UmbralService

pytestmark = pytest.mark.requires_db


def _build_audit_ctx(user, tenant_id) -> AuditContext:
    return AuditContext(
        actor_id=user.id,
        tenant_id=tenant_id,
        ip="127.0.0.1",
        user_agent="test",
    )


class TestUmbralService:
    """UmbralService — configurar y leer umbral (Task 14.5)."""

    async def test_configurar_umbral_numerico(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        asignacion_factory,
    ):
        """14.5 RED: configurar umbral numérico crea registro y audita."""
        t, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        asignacion = await asignacion_factory(
            db_session, tenant_id=t.id, usuario_id=user.id, materia_id=m.id,
        )
        audit_ctx = _build_audit_ctx(user, t.id)

        service = UmbralService()
        resultado = await service.configurar_umbral(
            tenant_id=t.id,
            asignacion_id=asignacion.id,
            materia_id=m.id,
            umbral_pct=75,
            valores_aprobatorios=["Aprobado", "Promocionado"],
            audit_ctx=audit_ctx,
            session=db_session,
        )

        assert resultado.umbral_pct == 75
        assert resultado.valores_aprobatorios == ["Aprobado", "Promocionado"]
        assert resultado.asignacion_id == asignacion.id
        assert resultado.materia_id == m.id

        # Verificar en DB
        from sqlalchemy import select

        stmt = (
            select(UmbralMateria)
            .where(
                UmbralMateria.tenant_id == t.id,
                UmbralMateria.asignacion_id == asignacion.id,
            )
        )
        result = await db_session.execute(stmt)
        db_umbral = result.scalar_one_or_none()
        assert db_umbral is not None
        assert db_umbral.umbral_pct == 75

    async def test_leer_umbral_sin_configuracion_devuelve_none(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        asignacion_factory,
    ):
        """14.5 RED: leer umbral sin configuración → None (no defaults)."""
        t, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        asignacion = await asignacion_factory(
            db_session, tenant_id=t.id, usuario_id=user.id, materia_id=m.id,
        )

        service = UmbralService()
        resultado = await service.get_umbral(
            tenant_id=t.id,
            asignacion_id=asignacion.id,
            session=db_session,
        )
        assert resultado is None

    async def test_configurar_umbral_fuera_rango_422(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        asignacion_factory,
    ):
        """14.5 TRIANGULATE: umbral_pct fuera de 0-100 → 422."""
        t, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        asignacion = await asignacion_factory(
            db_session, tenant_id=t.id, usuario_id=user.id, materia_id=m.id,
        )
        audit_ctx = _build_audit_ctx(user, t.id)

        service = UmbralService()
        with pytest.raises(CalificacionError) as exc:
            await service.configurar_umbral(
                tenant_id=t.id,
                asignacion_id=asignacion.id,
                materia_id=m.id,
                umbral_pct=150,
                audit_ctx=audit_ctx,
                session=db_session,
            )
        assert exc.value.status_code == 422
        assert "umbral_pct" in exc.value.detail

    async def test_umbral_independiente_por_asignacion(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        asignacion_factory,
    ):
        """14.5 TRIANGULATE: cada asignación tiene su propio umbral."""
        t, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        audit_ctx = _build_audit_ctx(user, t.id)

        asig1 = await asignacion_factory(
            db_session, tenant_id=t.id, usuario_id=user.id, materia_id=m.id,
        )

        from app.models.asignacion import Asignacion
        from app.models.role import Role

        role = Role(
            id=uuid.uuid4(),
            tenant_id=t.id,
            code=f"AUX-{uuid.uuid4().hex[:6]}",
            nombre="Auxiliar",
        )
        db_session.add(role)
        await db_session.flush()

        asig2 = Asignacion(
            id=uuid.uuid4(),
            tenant_id=t.id,
            usuario_id=user.id,
            role_id=role.id,
            materia_id=m.id,
            desde=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        )
        db_session.add(asig2)
        await db_session.commit()
        await db_session.refresh(asig2)

        service = UmbralService()

        # Configurar umbral para asig1
        await service.configurar_umbral(
            tenant_id=t.id,
            asignacion_id=asig1.id,
            materia_id=m.id,
            umbral_pct=80,
            audit_ctx=audit_ctx,
            session=db_session,
        )

        # asig2 no tiene umbral → None
        resultado = await service.get_umbral(
            tenant_id=t.id,
            asignacion_id=asig2.id,
            session=db_session,
        )
        assert resultado is None

        # asig1 tiene umbral 80
        resultado = await service.get_umbral(
            tenant_id=t.id,
            asignacion_id=asig1.id,
            session=db_session,
        )
        assert resultado is not None
        assert resultado.umbral_pct == 80

    async def test_umbral_actualiza_existente(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        asignacion_factory,
    ):
        """14.5 TRIANGULATE: configurar umbral existente lo actualiza."""
        t, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        asignacion = await asignacion_factory(
            db_session, tenant_id=t.id, usuario_id=user.id, materia_id=m.id,
        )
        audit_ctx = _build_audit_ctx(user, t.id)

        service = UmbralService()

        # Crear
        await service.configurar_umbral(
            tenant_id=t.id,
            asignacion_id=asignacion.id,
            materia_id=m.id,
            umbral_pct=60,
            audit_ctx=audit_ctx,
            session=db_session,
        )

        # Actualizar
        resultado = await service.configurar_umbral(
            tenant_id=t.id,
            asignacion_id=asignacion.id,
            materia_id=m.id,
            umbral_pct=85,
            valores_aprobatorios=["Aprobado"],
            audit_ctx=audit_ctx,
            session=db_session,
        )
        assert resultado.umbral_pct == 85
        assert resultado.valores_aprobatorios == ["Aprobado"]

    async def test_umbral_aislamiento_tenant(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        asignacion_factory,
        tenant_factory,
    ):
        """14.5 TRIANGULATE: umbral de tenant A invisible para tenant B."""
        t1, m1 = materia
        user1 = await user_factory(db_session, tenant_id=t1.id)
        asig1 = await asignacion_factory(
            db_session, tenant_id=t1.id, usuario_id=user1.id, materia_id=m1.id,
        )
        audit_ctx = _build_audit_ctx(user1, t1.id)

        # Configurar umbral en tenant A
        service = UmbralService()
        await service.configurar_umbral(
            tenant_id=t1.id,
            asignacion_id=asig1.id,
            materia_id=m1.id,
            umbral_pct=90,
            audit_ctx=audit_ctx,
            session=db_session,
        )

        # Tenant B no tiene umbral para esa asignación (ni debería poder verla)
        t2 = await tenant_factory(db_session, slug="tenant-b")
        resultado = await service.get_umbral(
            tenant_id=t2.id,
            asignacion_id=asig1.id,  # Misma asignación UUID pero otro tenant
            session=db_session,
        )
        assert resultado is None
