"""Tests for FechaAcademicaService."""

from datetime import datetime, timezone
from uuid import UUID

import pytest

from app.models.materia import Materia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte

pytestmark = pytest.mark.requires_db


class TestFechaAcademicaService:
    """RED: tests for FechaAcademicaService."""

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
        """Happy path: crear fecha con tipo enum válido."""
        from app.services.fecha_academica_service import FechaAcademicaService

        tenant, _, materia, cohorte = await self._setup(db_session, tenant_factory)
        service = FechaAcademicaService()

        result = await service.create(
            tenant_id=tenant.id,
            data={
                "materia_id": str(materia.id),
                "cohorte_id": str(cohorte.id),
                "tipo": "Parcial",
                "numero": 1,
                "periodo": "2026-1",
                "fecha": "2026-04-15T10:00:00Z",
                "titulo": "Primer Parcial",
            },
            session=db_session,
        )
        assert result.id is not None
        assert result.tipo == "Parcial"

    async def test_create_duplicate_fails(self, db_session, create_test_schema, tenant_factory):
        """Tipo+numero duplicado debe fallar con 409."""
        from app.services.fecha_academica_service import FechaAcademicaService, FechaAcademicaError

        tenant, _, materia, cohorte = await self._setup(db_session, tenant_factory)
        service = FechaAcademicaService()

        await service.create(
            tenant_id=tenant.id,
            data={
                "materia_id": str(materia.id), "cohorte_id": str(cohorte.id),
                "tipo": "Parcial", "numero": 1, "periodo": "2026-1",
                "fecha": "2026-04-15T10:00:00Z", "titulo": "P1",
            },
            session=db_session,
        )
        with pytest.raises(FechaAcademicaError) as exc:
            await service.create(
                tenant_id=tenant.id,
                data={
                    "materia_id": str(materia.id), "cohorte_id": str(cohorte.id),
                    "tipo": "Parcial", "numero": 1, "periodo": "2026-1",
                    "fecha": "2026-05-15T10:00:00Z", "titulo": "P1 dup",
                },
                session=db_session,
            )
        assert exc.value.status_code == 409

    async def test_create_materia_not_found_fails(self, db_session, create_test_schema, tenant_factory):
        """Materia inexistente debe fallar con 404."""
        from app.services.fecha_academica_service import FechaAcademicaService, FechaAcademicaError

        tenant, _, _, cohorte = await self._setup(db_session, tenant_factory)
        service = FechaAcademicaService()

        with pytest.raises(FechaAcademicaError) as exc:
            await service.create(
                tenant_id=tenant.id,
                data={
                    "materia_id": str(UUID("00000000-0000-0000-0000-000000000000")),
                    "cohorte_id": str(cohorte.id),
                    "tipo": "Parcial", "numero": 1, "periodo": "2026-1",
                    "fecha": "2026-04-15T10:00:00Z", "titulo": "No existe",
                },
                session=db_session,
            )
        assert exc.value.status_code == 404

    async def test_update_success(self, db_session, create_test_schema, tenant_factory):
        from app.services.fecha_academica_service import FechaAcademicaService

        tenant, _, materia, cohorte = await self._setup(db_session, tenant_factory)
        service = FechaAcademicaService()

        created = await service.create(
            tenant_id=tenant.id,
            data={
                "materia_id": str(materia.id), "cohorte_id": str(cohorte.id),
                "tipo": "TP", "numero": 1, "periodo": "2026-1",
                "fecha": "2026-04-15T10:00:00Z", "titulo": "TP Original",
            },
            session=db_session,
        )
        updated = await service.update(
            tenant_id=tenant.id,
            id=created.id,
            data={"titulo": "TP Actualizado"},
            session=db_session,
        )
        assert updated.titulo == "TP Actualizado"

    async def test_soft_delete_success(self, db_session, create_test_schema, tenant_factory):
        from app.services.fecha_academica_service import FechaAcademicaService

        tenant, _, materia, cohorte = await self._setup(db_session, tenant_factory)
        service = FechaAcademicaService()

        created = await service.create(
            tenant_id=tenant.id,
            data={
                "materia_id": str(materia.id), "cohorte_id": str(cohorte.id),
                "tipo": "Coloquio", "numero": 1, "periodo": "2026-1",
                "fecha": "2026-06-15T10:00:00Z", "titulo": "Coloquio",
            },
            session=db_session,
        )
        result = await service.delete(tenant_id=tenant.id, id=created.id, session=db_session)
        assert result is True

        deleted = await service.get(tenant_id=tenant.id, id=created.id, session=db_session)
        assert deleted is None

    async def test_list_tabular_ordered(self, db_session, create_test_schema, tenant_factory):
        from app.services.fecha_academica_service import FechaAcademicaService

        tenant, _, materia, cohorte = await self._setup(db_session, tenant_factory)
        service = FechaAcademicaService()

        await service.create(
            tenant_id=tenant.id,
            data={
                "materia_id": str(materia.id), "cohorte_id": str(cohorte.id),
                "tipo": "Parcial", "numero": 2, "periodo": "2026-1",
                "fecha": "2026-05-15T10:00:00Z", "titulo": "P2",
            },
            session=db_session,
        )
        await service.create(
            tenant_id=tenant.id,
            data={
                "materia_id": str(materia.id), "cohorte_id": str(cohorte.id),
                "tipo": "Parcial", "numero": 1, "periodo": "2026-1",
                "fecha": "2026-04-15T10:00:00Z", "titulo": "P1",
            },
            session=db_session,
        )

        results = await service.list_tabular(tenant_id=tenant.id, session=db_session, materia_id=materia.id)
        assert len(results) == 2
        assert results[0].titulo == "P1"  # earlier date first

    async def test_list_calendario_grouped(self, db_session, create_test_schema, tenant_factory):
        from app.services.fecha_academica_service import FechaAcademicaService

        tenant, _, materia, cohorte = await self._setup(db_session, tenant_factory)
        service = FechaAcademicaService()

        await service.create(
            tenant_id=tenant.id,
            data={
                "materia_id": str(materia.id), "cohorte_id": str(cohorte.id),
                "tipo": "Parcial", "numero": 1, "periodo": "2026-1",
                "fecha": "2026-04-15T10:00:00Z", "titulo": "P1",
            },
            session=db_session,
        )
        await service.create(
            tenant_id=tenant.id,
            data={
                "materia_id": str(materia.id), "cohorte_id": str(cohorte.id),
                "tipo": "TP", "numero": 1, "periodo": "2026-2",
                "fecha": "2026-08-15T10:00:00Z", "titulo": "TP1 S2",
            },
            session=db_session,
        )

        calendario = await service.list_calendario(tenant_id=tenant.id, session=db_session, materia_id=materia.id)
        assert len(calendario) == 2
        periodos = {c["periodo"] for c in calendario}
        assert periodos == {"2026-1", "2026-2"}

    async def test_build_lms_fragment_with_fechas(self, db_session, create_test_schema, tenant_factory):
        """build_lms_fragment produce texto ordenado para ≥2 fechas."""
        from app.services.fecha_academica_service import build_lms_fragment
        from app.models.fecha_academica import FechaAcademica

        tenant, _, materia, cohorte = await self._setup(db_session, tenant_factory)
        from app.models.fecha_academica import TipoFechaAcademica

        f1 = FechaAcademica(
            tenant_id=tenant.id, materia_id=materia.id, cohorte_id=cohorte.id,
            tipo=TipoFechaAcademica.Parcial, numero=1, periodo="2026-1",
            fecha=datetime(2026, 4, 15, 10, 0, 0, tzinfo=timezone.utc),
            titulo="Primer Parcial",
        )
        f2 = FechaAcademica(
            tenant_id=tenant.id, materia_id=materia.id, cohorte_id=cohorte.id,
            tipo=TipoFechaAcademica.TP, numero=1, periodo="2026-1",
            fecha=datetime(2026, 5, 10, 10, 0, 0, tzinfo=timezone.utc),
            titulo="TP 1",
        )
        fragment = build_lms_fragment([f2, f1])  # desordenado a propósito
        assert "Parcial" in fragment
        assert "TP" in fragment
        # Check ordering by date
        idx_p1 = fragment.index("Primer Parcial")
        idx_tp = fragment.index("TP 1")
        assert idx_p1 < idx_tp  # April before May

    async def test_build_lms_fragment_empty(self):
        """build_lms_fragment con lista vacía retorna texto informativo."""
        from app.services.fecha_academica_service import build_lms_fragment

        fragment = build_lms_fragment([])
        assert "sin evaluaciones" in fragment.lower()

    async def test_build_lms_fragment_single(self, db_session, create_test_schema, tenant_factory):
        """build_lms_fragment con 1 fecha."""
        from app.services.fecha_academica_service import build_lms_fragment
        from app.models.fecha_academica import FechaAcademica, TipoFechaAcademica
        from datetime import datetime, timezone

        tenant, _, materia, cohorte = await self._setup(db_session, tenant_factory)
        f1 = FechaAcademica(
            tenant_id=tenant.id, materia_id=materia.id, cohorte_id=cohorte.id,
            tipo=TipoFechaAcademica.Parcial, numero=1, periodo="2026-1",
            fecha=datetime(2026, 4, 15, 10, 0, 0, tzinfo=timezone.utc),
            titulo="Parcial 1",
        )
        fragment = build_lms_fragment([f1])
        assert "Parcial 1" in fragment
        assert "15/04" in fragment or "2026-04" in fragment
