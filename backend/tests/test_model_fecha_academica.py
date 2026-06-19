"""Tests for FechaAcademica model."""

from datetime import datetime, timezone

import pytest

from app.models.materia import Materia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte

pytestmark = pytest.mark.requires_db


class TestFechaAcademicaModel:
    """RED: test de modelo FechaAcademica — persistir con columnas y mixin base."""

    async def _make_carrera_cohorte(self, db_session, tenant):
        carrera = Carrera(tenant_id=tenant.id, codigo="FC1", nombre="Carrera FA")
        db_session.add(carrera)
        await db_session.flush()
        cohorte = Cohorte(
            tenant_id=tenant.id, carrera_id=carrera.id,
            nombre="Coh FA", anio=2026, vig_desde="2026-01-01",
        )
        db_session.add(cohorte)
        await db_session.flush()
        return carrera, cohorte

    async def test_create_and_persist(self, db_session, create_test_schema, tenant_factory):
        """Persistir FechaAcademica con todos los campos y mixin base."""
        from app.models.fecha_academica import FechaAcademica, TipoFechaAcademica

        tenant = await tenant_factory(db_session)
        materia = Materia(tenant_id=tenant.id, codigo="M1", nombre="Materia Test")
        db_session.add(materia)
        _, cohorte = await self._make_carrera_cohorte(db_session, tenant)
        await db_session.flush()

        fecha = FechaAcademica(
            tenant_id=tenant.id,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            tipo=TipoFechaAcademica.Parcial,
            numero=1,
            periodo="2026-1",
            fecha=datetime(2026, 4, 15, 10, 0, 0, tzinfo=timezone.utc),
            titulo="Primer Parcial",
        )
        db_session.add(fecha)
        await db_session.flush()
        await db_session.refresh(fecha)

        assert fecha.id is not None
        assert fecha.tenant_id == tenant.id
        assert fecha.created_at is not None
        assert fecha.updated_at is not None
        assert fecha.deleted_at is None
        assert fecha.tipo == TipoFechaAcademica.Parcial
        assert fecha.numero == 1
        assert fecha.periodo == "2026-1"

    async def test_unique_same_tipo_numero_fails(self, db_session, create_test_schema, tenant_factory):
        """Mismo tipo + numero para misma materia×cohorte viola unique constraint."""
        from app.models.fecha_academica import FechaAcademica, TipoFechaAcademica

        tenant = await tenant_factory(db_session)
        materia = Materia(tenant_id=tenant.id, codigo="M2", nombre="Mat 2")
        db_session.add(materia)
        _, cohorte = await self._make_carrera_cohorte(db_session, tenant)
        await db_session.flush()

        f1 = FechaAcademica(
            tenant_id=tenant.id, materia_id=materia.id, cohorte_id=cohorte.id,
            tipo=TipoFechaAcademica.Parcial, numero=1,
            periodo="2026-1", fecha=datetime(2026, 4, 15, 10, 0, 0, tzinfo=timezone.utc),
            titulo="Parcial 1",
        )
        db_session.add(f1)
        await db_session.flush()

        f2 = FechaAcademica(
            tenant_id=tenant.id, materia_id=materia.id, cohorte_id=cohorte.id,
            tipo=TipoFechaAcademica.Parcial, numero=1,
            periodo="2026-1", fecha=datetime(2026, 5, 15, 10, 0, 0, tzinfo=timezone.utc),
            titulo="Parcial 1 dup",
        )
        db_session.add(f2)
        with pytest.raises(Exception):
            await db_session.flush()

    async def test_same_tipo_different_numero_ok(self, db_session, create_test_schema, tenant_factory):
        """Mismo tipo, distinto numero — OK (no viola unique)."""
        from app.models.fecha_academica import FechaAcademica, TipoFechaAcademica

        tenant = await tenant_factory(db_session)
        materia = Materia(tenant_id=tenant.id, codigo="M3", nombre="Mat 3")
        db_session.add(materia)
        _, cohorte = await self._make_carrera_cohorte(db_session, tenant)
        await db_session.flush()

        f1 = FechaAcademica(
            tenant_id=tenant.id, materia_id=materia.id, cohorte_id=cohorte.id,
            tipo=TipoFechaAcademica.Parcial, numero=1,
            periodo="2026-1", fecha=datetime(2026, 4, 15, 10, 0, 0, tzinfo=timezone.utc),
            titulo="Parcial 1",
        )
        db_session.add(f1)
        await db_session.flush()

        f2 = FechaAcademica(
            tenant_id=tenant.id, materia_id=materia.id, cohorte_id=cohorte.id,
            tipo=TipoFechaAcademica.Parcial, numero=2,
            periodo="2026-1", fecha=datetime(2026, 6, 15, 10, 0, 0, tzinfo=timezone.utc),
            titulo="Parcial 2",
        )
        db_session.add(f2)
        await db_session.flush()

        assert f1.id != f2.id
