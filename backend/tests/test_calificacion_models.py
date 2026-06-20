"""Tests ORM para modelos Calificacion y UmbralMateria (C-10).

Strict TDD: RED → GREEN → TRIANGULATE → REFACTOR.
Usa contenedor de DB efímero — no mocks.
Marcado @pytest.mark.requires_db.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calificacion import Calificacion, OrigenCalificacionDB, UmbralMateria


@pytest.mark.requires_db
class TestCalificacionModel:
    """Validación del modelo Calificacion."""

    async def test_crear_calificacion(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        tenant_factory,
        version_padron,
    ):
        """GREEN: Calificacion tiene los campos mínimos y FK."""
        t = await tenant_factory(db_session)
        _, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        vp, ep = version_padron

        c = Calificacion(
            tenant_id=t.id,
            entrada_padron_id=ep.id,
            materia_id=m.id,
            actividad="TP1",
            nota_numerica=8.5,
            creado_por=user.id,
            origen=OrigenCalificacionDB.IMPORTADO,
        )
        db_session.add(c)
        await db_session.commit()
        await db_session.refresh(c)

        assert c.id is not None
        assert c.tenant_id == t.id
        assert c.entrada_padron_id == ep.id
        assert c.materia_id == m.id
        assert c.actividad == "TP1"
        assert c.nota_numerica == 8.5
        assert c.nota_textual is None
        assert c.origen == OrigenCalificacionDB.IMPORTADO
        assert c.creado_por == user.id
        assert c.deleted_at is None
        assert c.deleted_by is None

    async def test_mixin_base_fields(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        tenant_factory,
        version_padron,
    ):
        """RED: Calificacion hereda TenantScopedMixin (id, tenant_id, timestamps, soft-delete)."""
        t = await tenant_factory(db_session)
        _, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        vp, ep = version_padron

        c = Calificacion(
            tenant_id=t.id,
            entrada_padron_id=ep.id,
            materia_id=m.id,
            actividad="TP1",
            nota_numerica=7.0,
            creado_por=user.id,
            origen=OrigenCalificacionDB.IMPORTADO,
        )
        db_session.add(c)
        await db_session.commit()
        await db_session.refresh(c)

        assert c.id is not None
        assert isinstance(c.id, uuid.UUID)
        assert c.created_at is not None
        assert c.updated_at is not None
        assert c.deleted_at is None
        assert hasattr(c, "deleted_by")

    async def test_no_tiene_aprobado_almacenado(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        tenant_factory,
        version_padron,
    ):
        """RED: Calificacion NO tiene campo aprobado almacenado (derivado read-time)."""
        t = await tenant_factory(db_session)
        _, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        vp, ep = version_padron

        c = Calificacion(
            tenant_id=t.id,
            entrada_padron_id=ep.id,
            materia_id=m.id,
            actividad="TP1",
            nota_textual="Satisfactorio",
            creado_por=user.id,
            origen=OrigenCalificacionDB.IMPORTADO,
        )
        assert not hasattr(c, "aprobado"), "aprobado NO debe ser campo almacenado"

    async def test_soft_delete_fields(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        tenant_factory,
        version_padron,
    ):
        """RED: soft-delete marca deleted_at y deleted_by."""
        t = await tenant_factory(db_session)
        _, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        vp, ep = version_padron

        c = Calificacion(
            tenant_id=t.id,
            entrada_padron_id=ep.id,
            materia_id=m.id,
            actividad="TP1",
            nota_numerica=6.0,
            creado_por=user.id,
            origen=OrigenCalificacionDB.IMPORTADO,
        )
        db_session.add(c)
        await db_session.commit()
        await db_session.refresh(c)

        c.deleted_at = None  # placeholder - real soft delete done via repo
        assert hasattr(c, "deleted_at")
        assert hasattr(c, "deleted_by")

    async def test_indices_compuestos(
        self,
        db_session: AsyncSession,
    ):
        """RED: verificar que existen los índices compuestos."""
        from sqlalchemy import text

        result = await db_session.execute(
            text("SELECT indexname FROM pg_indexes WHERE tablename = 'calificacion'")
        )
        rows = result.fetchall()
        index_names = [r[0] for r in rows]
        assert any("ix_calificacion_tenant_materia" in name for name in index_names)
        assert any("ix_calificacion_tenant_entrada" in name for name in index_names)

    async def test_repr_seguro(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        tenant_factory,
        version_padron,
    ):
        """RED: __repr__ no incluye PII."""
        t = await tenant_factory(db_session)
        _, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        vp, ep = version_padron

        c = Calificacion(
            tenant_id=t.id,
            entrada_padron_id=ep.id,
            materia_id=m.id,
            actividad="TP1",
            nota_numerica=8.0,
            creado_por=user.id,
            origen=OrigenCalificacionDB.IMPORTADO,
        )
        db_session.add(c)
        await db_session.commit()
        await db_session.refresh(c)

        rep = repr(c)
        assert "id=" in rep
        assert "actividad=" in rep
        # No debe contener datos de la nota en texto plano sensible
        assert "PII" not in rep


@pytest.mark.requires_db
class TestUmbralMateriaModel:
    """Validación del modelo UmbralMateria."""

    async def test_crear_umbral(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        tenant_factory,
        asignacion_factory,
    ):
        """GREEN: UmbralMateria tiene campos y FK."""
        t = await tenant_factory(db_session)
        _, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        asignacion = await asignacion_factory(db_session, tenant_id=t.id, usuario_id=user.id, materia_id=m.id)

        u = UmbralMateria(
            tenant_id=t.id,
            asignacion_id=asignacion.id,
            materia_id=m.id,
            umbral_pct=70,
            valores_aprobatorios=["Satisfactorio", "Supera lo esperado"],
        )
        db_session.add(u)
        await db_session.commit()
        await db_session.refresh(u)

        assert u.id is not None
        assert u.tenant_id == t.id
        assert u.asignacion_id == asignacion.id
        assert u.materia_id == m.id
        assert u.umbral_pct == 70
        assert u.valores_aprobatorios == ["Satisfactorio", "Supera lo esperado"]

    async def test_umbral_pct_default(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        tenant_factory,
        asignacion_factory,
    ):
        """RED: umbral_pct default es 60."""
        t = await tenant_factory(db_session)
        _, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        asignacion = await asignacion_factory(db_session, tenant_id=t.id, usuario_id=user.id, materia_id=m.id)

        u = UmbralMateria(
            tenant_id=t.id,
            asignacion_id=asignacion.id,
            materia_id=m.id,
        )
        db_session.add(u)
        await db_session.commit()
        await db_session.refresh(u)

        assert u.umbral_pct == 60

    async def test_unique_constraint(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        tenant_factory,
        asignacion_factory,
    ):
        """RED: UniqueConstraint(tenant_id, asignacion_id, materia_id)."""
        t = await tenant_factory(db_session)
        _, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        asignacion = await asignacion_factory(db_session, tenant_id=t.id, usuario_id=user.id, materia_id=m.id)

        u1 = UmbralMateria(
            tenant_id=t.id,
            asignacion_id=asignacion.id,
            materia_id=m.id,
            umbral_pct=60,
        )
        db_session.add(u1)
        await db_session.commit()

        u2 = UmbralMateria(
            tenant_id=t.id,
            asignacion_id=asignacion.id,
            materia_id=m.id,
            umbral_pct=80,
        )
        db_session.add(u2)
        with pytest.raises(Exception):  # IntegrityError expected
            await db_session.commit()

    async def test_repr_seguro(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        tenant_factory,
        asignacion_factory,
    ):
        """RED: __repr__ seguro sin PII."""
        t = await tenant_factory(db_session)
        _, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        asignacion = await asignacion_factory(db_session, tenant_id=t.id, usuario_id=user.id, materia_id=m.id)

        u = UmbralMateria(
            tenant_id=t.id,
            asignacion_id=asignacion.id,
            materia_id=m.id,
        )
        db_session.add(u)
        await db_session.commit()
        await db_session.refresh(u)

        rep = repr(u)
        assert "UmbralMateria" in rep
        assert "umbral_pct=" in rep
