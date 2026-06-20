"""Tests para UmbralRepository.

Strict TDD: RED → GREEN → TRIANGULATE → REFACTOR.
Casos cubiertos: get_by_asignacion (existe/no existe/otro tenant),
upsert (crear nuevo/actualizar existente).
"""

from __future__ import annotations

import uuid

import pytest

from app.models.calificacion import UmbralMateria
from app.repositories.umbral_repository import UmbralRepository

pytestmark = pytest.mark.requires_db


class TestGetByAsignacion:
    """Grupo 6.1-6.2: get_by_asignacion."""

    async def test_devuelve_umbral_cuando_existe(
        self, db_session, materia, asignacion_factory, user_factory,
    ):
        t, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        asignacion = await asignacion_factory(
            db_session, tenant_id=t.id, materia_id=m.id, usuario_id=user.id,
        )
        repo = UmbralRepository()

        umbral = UmbralMateria(
            id=uuid.uuid4(),
            tenant_id=t.id,
            asignacion_id=asignacion.id,
            materia_id=m.id,
            umbral_pct=75,
        )
        db_session.add(umbral)
        await db_session.commit()

        result = await repo.get_by_asignacion(
            tenant_id=t.id,
            asignacion_id=asignacion.id,
            session=db_session,
        )
        assert result is not None
        assert result.id == umbral.id
        assert result.umbral_pct == 75

    async def test_retorna_none_si_no_existe(
        self, db_session, asignacion_factory,
    ):
        t_id = uuid.uuid4()
        repo = UmbralRepository()

        result = await repo.get_by_asignacion(
            tenant_id=t_id,
            asignacion_id=uuid.uuid4(),
            session=db_session,
        )
        assert result is None

    async def test_excluye_umbral_de_otro_tenant(
        self, db_session, materia, asignacion_factory, tenant_factory, user_factory,
    ):
        t, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        asignacion = await asignacion_factory(
            db_session, tenant_id=t.id, materia_id=m.id, usuario_id=user.id,
        )
        other_t = await tenant_factory(db_session, slug=f"other-{uuid.uuid4().hex[:8]}")
        repo = UmbralRepository()

        umbral = UmbralMateria(
            id=uuid.uuid4(),
            tenant_id=t.id,
            asignacion_id=asignacion.id,
            materia_id=m.id,
            umbral_pct=60,
        )
        db_session.add(umbral)
        await db_session.commit()

        result = await repo.get_by_asignacion(
            tenant_id=other_t.id,
            asignacion_id=asignacion.id,
            session=db_session,
        )
        assert result is None


class TestUpsert:
    """Grupo 6.3-6.4: upsert."""

    async def test_crea_nuevo_umbral(
        self, db_session, materia, asignacion_factory, user_factory,
    ):
        t, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        asignacion = await asignacion_factory(
            db_session, tenant_id=t.id, materia_id=m.id, usuario_id=user.id,
        )
        repo = UmbralRepository()

        result = await repo.upsert(
            tenant_id=t.id,
            asignacion_id=asignacion.id,
            materia_id=m.id,
            umbral_pct=80,
            session=db_session,
        )
        assert result is not None
        assert result.umbral_pct == 80
        assert result.tenant_id == t.id
        assert result.asignacion_id == asignacion.id
        assert result.materia_id == m.id

    async def test_actualiza_umbral_existente(
        self, db_session, materia, asignacion_factory, user_factory,
    ):
        t, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        asignacion = await asignacion_factory(
            db_session, tenant_id=t.id, materia_id=m.id, usuario_id=user.id,
        )
        repo = UmbralRepository()

        # Crear inicial
        original = await repo.upsert(
            tenant_id=t.id,
            asignacion_id=asignacion.id,
            materia_id=m.id,
            umbral_pct=60,
            session=db_session,
        )
        original_id = original.id

        # Actualizar
        updated = await repo.upsert(
            tenant_id=t.id,
            asignacion_id=asignacion.id,
            materia_id=m.id,
            umbral_pct=90,
            session=db_session,
        )
        assert updated.id == original_id
        assert updated.umbral_pct == 90

    async def test_upsert_con_valores_aprobatorios(
        self, db_session, materia, asignacion_factory, user_factory,
    ):
        t, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        asignacion = await asignacion_factory(
            db_session, tenant_id=t.id, materia_id=m.id, usuario_id=user.id,
        )
        repo = UmbralRepository()

        result = await repo.upsert(
            tenant_id=t.id,
            asignacion_id=asignacion.id,
            materia_id=m.id,
            umbral_pct=70,
            valores_aprobatorios=["Satisfactorio", "Supera lo esperado"],
            session=db_session,
        )
        assert result.valores_aprobatorios == ["Satisfactorio", "Supera lo esperado"]
