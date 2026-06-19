"""Tests for ProgramaMateria model."""

import uuid

import pytest

from app.models.materia import Materia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte

pytestmark = pytest.mark.requires_db


class TestProgramaMateriaModel:
    """RED: test de modelo ProgramaMateria — instanciar y persistir."""

    async def _make_entities(self, db_session, tenant):
        carrera = Carrera(tenant_id=tenant.id, codigo="C1", nombre="Carrera Test")
        db_session.add(carrera)
        await db_session.flush()
        materia = Materia(tenant_id=tenant.id, codigo="M1", nombre="Materia Test")
        db_session.add(materia)
        await db_session.flush()
        cohorte = Cohorte(
            tenant_id=tenant.id, carrera_id=carrera.id,
            nombre="Cohorte A", anio=2026, vig_desde="2026-01-01",
        )
        db_session.add(cohorte)
        await db_session.flush()
        return carrera, materia, cohorte

    async def test_create_and_persist(self, db_session, create_test_schema, tenant_factory):
        """Persistir un ProgramaMateria con todas sus columnas y mixin base."""
        from app.models.programa_materia import ProgramaMateria

        tenant = await tenant_factory(db_session)
        carrera, materia, cohorte = await self._make_entities(db_session, tenant)

        programa = ProgramaMateria(
            tenant_id=tenant.id,
            materia_id=materia.id,
            carrera_id=carrera.id,
            cohorte_id=cohorte.id,
            titulo="Programa de Materia Test",
            referencia_archivo="storage://tenant-a/programas/prog-2026.pdf",
        )
        db_session.add(programa)
        await db_session.flush()
        await db_session.refresh(programa)

        assert programa.id is not None
        assert programa.tenant_id == tenant.id
        assert programa.created_at is not None
        assert programa.updated_at is not None
        assert programa.deleted_at is None
        assert programa.materia_id == materia.id
        assert programa.carrera_id == carrera.id
        assert programa.cohorte_id == cohorte.id
        assert programa.titulo == "Programa de Materia Test"
        assert programa.referencia_archivo == "storage://tenant-a/programas/prog-2026.pdf"
        assert programa.cargado_at is not None

    async def test_fails_without_fk(self, db_session, create_test_schema, tenant_factory):
        """FK inexistente debe lanzar error de integridad."""
        from app.models.programa_materia import ProgramaMateria

        tenant = await tenant_factory(db_session)
        programa = ProgramaMateria(
            tenant_id=tenant.id,
            materia_id=uuid.uuid4(),
            carrera_id=uuid.uuid4(),
            cohorte_id=uuid.uuid4(),
            titulo="Sin FK",
        )
        db_session.add(programa)
        with pytest.raises(Exception):
            await db_session.flush()

    async def test_unique_constraint_different_combinations_ok(self, db_session, create_test_schema, tenant_factory):
        """Combinaciones distintas NO disparan unique constraint."""
        from app.models.programa_materia import ProgramaMateria

        tenant = await tenant_factory(db_session)
        carrera, materia, cohorte = await self._make_entities(db_session, tenant)

        # Otra carrera, misma materia y cohorte
        carrera2 = Carrera(tenant_id=tenant.id, codigo="C2", nombre="Carrera 2")
        db_session.add(carrera2)
        await db_session.flush()

        p1 = ProgramaMateria(
            tenant_id=tenant.id, materia_id=materia.id,
            carrera_id=carrera.id, cohorte_id=cohorte.id,
            titulo="Programa 1",
        )
        db_session.add(p1)
        await db_session.flush()

        p2 = ProgramaMateria(
            tenant_id=tenant.id, materia_id=materia.id,
            carrera_id=carrera2.id, cohorte_id=cohorte.id,
            titulo="Programa 2",
        )
        db_session.add(p2)
        await db_session.flush()

        assert p1.id != p2.id
