"""Tests for ProgramaMateriaService."""

import uuid

import pytest

from app.models.materia import Materia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte

pytestmark = pytest.mark.requires_db


class TestProgramaMateriaService:
    """RED: tests for ProgramaMateriaService."""

    async def _setup(self, db_session, tenant_factory):
        tenant = await tenant_factory(db_session)
        carrera = Carrera(tenant_id=tenant.id, codigo="C1", nombre="C Test")
        db_session.add(carrera)
        await db_session.flush()
        materia = Materia(tenant_id=tenant.id, codigo="M1", nombre="M Test")
        db_session.add(materia)
        await db_session.flush()
        cohorte = Cohorte(
            tenant_id=tenant.id, carrera_id=carrera.id,
            nombre="Coh A", anio=2026, vig_desde="2026-01-01",
        )
        db_session.add(cohorte)
        await db_session.flush()
        return tenant, carrera, materia, cohorte

    async def test_create_success(self, db_session, create_test_schema, tenant_factory):
        """Happy path: crear programa con combinación nueva."""
        from app.services.programa_materia_service import ProgramaMateriaService

        tenant, carrera, materia, cohorte = await self._setup(db_session, tenant_factory)
        service = ProgramaMateriaService()

        result = await service.create(
            tenant_id=tenant.id,
            data={
                "materia_id": str(materia.id),
                "carrera_id": str(carrera.id),
                "cohorte_id": str(cohorte.id),
                "titulo": "Programa de Álgebra",
                "referencia_archivo": "storage://ref/prog.pdf",
            },
            session=db_session,
        )
        assert result.id is not None
        assert result.titulo == "Programa de Álgebra"
        assert result.cargado_at is not None

    async def test_create_duplicate_fails(self, db_session, create_test_schema, tenant_factory):
        """Combinación duplicada debe fallar con 409."""
        from app.services.programa_materia_service import ProgramaMateriaService, ServiceError

        tenant, carrera, materia, cohorte = await self._setup(db_session, tenant_factory)
        service = ProgramaMateriaService()

        await service.create(
            tenant_id=tenant.id,
            data={
                "materia_id": str(materia.id),
                "carrera_id": str(carrera.id),
                "cohorte_id": str(cohorte.id),
                "titulo": "Original",
            },
            session=db_session,
        )

        with pytest.raises(ServiceError) as exc:
            await service.create(
                tenant_id=tenant.id,
                data={
                    "materia_id": str(materia.id),
                    "carrera_id": str(carrera.id),
                    "cohorte_id": str(cohorte.id),
                    "titulo": "Duplicado",
                },
                session=db_session,
            )
        assert exc.value.status_code == 409

    async def test_create_materia_not_found_fails(self, db_session, create_test_schema, tenant_factory):
        """Materia inexistente debe fallar con 404."""
        from app.services.programa_materia_service import ProgramaMateriaService, ServiceError

        tenant, carrera, _, cohorte = await self._setup(db_session, tenant_factory)
        service = ProgramaMateriaService()

        with pytest.raises(ServiceError) as exc:
            await service.create(
                tenant_id=tenant.id,
                data={
                    "materia_id": str(uuid.uuid4()),
                    "carrera_id": str(carrera.id),
                    "cohorte_id": str(cohorte.id),
                    "titulo": "No existe",
                },
                session=db_session,
            )
        assert exc.value.status_code == 404

    async def test_get_success(self, db_session, create_test_schema, tenant_factory):
        from app.services.programa_materia_service import ProgramaMateriaService

        tenant, carrera, materia, cohorte = await self._setup(db_session, tenant_factory)
        service = ProgramaMateriaService()

        created = await service.create(
            tenant_id=tenant.id,
            data={
                "materia_id": str(materia.id),
                "carrera_id": str(carrera.id),
                "cohorte_id": str(cohorte.id),
                "titulo": "Test",
            },
            session=db_session,
        )
        found = await service.get(tenant_id=tenant.id, id=created.id, session=db_session)
        assert found.id == created.id

    async def test_get_not_found_fails(self, db_session, create_test_schema, tenant_factory):
        from app.services.programa_materia_service import ProgramaMateriaService, ServiceError

        tenant, _, _, _ = await self._setup(db_session, tenant_factory)
        service = ProgramaMateriaService()

        with pytest.raises(ServiceError) as exc:
            await service.get(tenant_id=tenant.id, id=uuid.uuid4(), session=db_session)
        assert exc.value.status_code == 404

    async def test_update_success(self, db_session, create_test_schema, tenant_factory):
        from app.services.programa_materia_service import ProgramaMateriaService

        tenant, carrera, materia, cohorte = await self._setup(db_session, tenant_factory)
        service = ProgramaMateriaService()

        created = await service.create(
            tenant_id=tenant.id,
            data={
                "materia_id": str(materia.id),
                "carrera_id": str(carrera.id),
                "cohorte_id": str(cohorte.id),
                "titulo": "Original",
            },
            session=db_session,
        )
        updated = await service.update(
            tenant_id=tenant.id,
            id=created.id,
            data={"titulo": "Actualizado"},
            session=db_session,
        )
        assert updated.titulo == "Actualizado"

    async def test_soft_delete_success(self, db_session, create_test_schema, tenant_factory):
        from app.services.programa_materia_service import ProgramaMateriaService

        tenant, carrera, materia, cohorte = await self._setup(db_session, tenant_factory)
        service = ProgramaMateriaService()

        created = await service.create(
            tenant_id=tenant.id,
            data={
                "materia_id": str(materia.id),
                "carrera_id": str(carrera.id),
                "cohorte_id": str(cohorte.id),
                "titulo": "Para borrar",
            },
            session=db_session,
        )
        result = await service.delete(tenant_id=tenant.id, id=created.id, session=db_session)
        assert result is True

        with pytest.raises(Exception):
            await service.get(tenant_id=tenant.id, id=created.id, session=db_session)

    async def test_list_with_filters(self, db_session, create_test_schema, tenant_factory):
        from app.services.programa_materia_service import ProgramaMateriaService

        tenant, carrera, materia, cohorte = await self._setup(db_session, tenant_factory)
        service = ProgramaMateriaService()

        await service.create(
            tenant_id=tenant.id,
            data={
                "materia_id": str(materia.id),
                "carrera_id": str(carrera.id),
                "cohorte_id": str(cohorte.id),
                "titulo": "P1",
            },
            session=db_session,
        )

        results = await service.list(tenant_id=tenant.id, session=db_session, cohorte_id=cohorte.id)
        assert len(results) == 1
        assert results[0].titulo == "P1"
