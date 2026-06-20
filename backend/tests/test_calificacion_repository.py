"""Tests para CalificacionRepository.

Strict TDD: RED → GREEN → TRIANGULATE → REFACTOR.
Casos cubiertos: scoping por tenant, soft-delete exclusion, bulk insert,
soft-delete_by_materia_y_usuario, get_by_entrada_padron.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import func, update

from app.models.calificacion import Calificacion, OrigenCalificacionDB
from app.repositories.calificacion_repository import CalificacionRepository

pytestmark = pytest.mark.requires_db


class TestGetByMateriaYUsuario:
    """Grupo 5.1-5.2: get_by_materia_y_usuario."""

    async def test_devuelve_calificaciones_de_usuario(
        self, db_session, materia, version_padron, user_factory,
    ):
        t, m = materia
        _, ep = version_padron
        user = await user_factory(db_session, tenant_id=t.id)
        repo = CalificacionRepository()

        c1 = Calificacion(
            id=uuid.uuid4(),
            tenant_id=t.id,
            entrada_padron_id=ep.id,
            materia_id=m.id,
            actividad="TP1",
            nota_numerica=85.0,
            origen=OrigenCalificacionDB.IMPORTADO,
            creado_por=user.id,
        )
        c2 = Calificacion(
            id=uuid.uuid4(),
            tenant_id=t.id,
            entrada_padron_id=ep.id,
            materia_id=m.id,
            actividad="TP2",
            nota_numerica=90.0,
            origen=OrigenCalificacionDB.IMPORTADO,
            creado_por=user.id,
        )
        db_session.add_all([c1, c2])
        await db_session.commit()

        result = await repo.get_by_materia_y_usuario(
            tenant_id=t.id,
            materia_id=m.id,
            creado_por=user.id,
            session=db_session,
        )
        assert len(result) == 2
        ids = {r.id for r in result}
        assert c1.id in ids
        assert c2.id in ids

    async def test_retorna_lista_vacia_sin_datos(
        self, db_session, materia, user_factory,
    ):
        t, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        repo = CalificacionRepository()

        result = await repo.get_by_materia_y_usuario(
            tenant_id=t.id,
            materia_id=m.id,
            creado_por=user.id,
            session=db_session,
        )
        assert result == []

    async def test_excluye_calificaciones_de_otro_tenant(
        self, db_session, materia, version_padron, user_factory, tenant_factory,
    ):
        t, m = materia
        _, ep = version_padron
        user = await user_factory(db_session, tenant_id=t.id)
        other_t = await tenant_factory(db_session, slug=f"other-{uuid.uuid4().hex[:8]}")
        repo = CalificacionRepository()

        c = Calificacion(
            id=uuid.uuid4(),
            tenant_id=t.id,
            entrada_padron_id=ep.id,
            materia_id=m.id,
            actividad="TP1",
            nota_numerica=85.0,
            origen=OrigenCalificacionDB.IMPORTADO,
            creado_por=user.id,
        )
        db_session.add(c)
        await db_session.commit()

        result = await repo.get_by_materia_y_usuario(
            tenant_id=other_t.id,
            materia_id=m.id,
            creado_por=user.id,
            session=db_session,
        )
        assert result == []

    async def test_excluye_soft_deleted(
        self, db_session, materia, version_padron, user_factory,
    ):
        t, m = materia
        _, ep = version_padron
        user = await user_factory(db_session, tenant_id=t.id)
        repo = CalificacionRepository()

        c = Calificacion(
            id=uuid.uuid4(),
            tenant_id=t.id,
            entrada_padron_id=ep.id,
            materia_id=m.id,
            actividad="TP1",
            nota_numerica=85.0,
            origen=OrigenCalificacionDB.IMPORTADO,
            creado_por=user.id,
        )
        db_session.add(c)
        await db_session.commit()

        # Soft-delete via UPDATE directo
        stmt = (
            update(Calificacion)
            .where(Calificacion.id == c.id)
            .values(deleted_at=func.now())
            .returning(Calificacion.id)
        )
        await db_session.execute(stmt)
        await db_session.commit()

        result = await repo.get_by_materia_y_usuario(
            tenant_id=t.id,
            materia_id=m.id,
            creado_por=user.id,
            session=db_session,
        )
        assert result == []


class TestBulkCreate:
    """Grupo 5.3-5.4: bulk_create."""

    async def test_inserta_varias_calificaciones(
        self, db_session, materia, version_padron, user_factory,
    ):
        t, m = materia
        _, ep = version_padron
        user = await user_factory(db_session, tenant_id=t.id)
        repo = CalificacionRepository()

        calificaciones = [
            Calificacion(
                id=uuid.uuid4(),
                tenant_id=t.id,
                entrada_padron_id=ep.id,
                materia_id=m.id,
                actividad="TP1",
                nota_numerica=80.0,
                origen=OrigenCalificacionDB.IMPORTADO,
                creado_por=user.id,
            ),
            Calificacion(
                id=uuid.uuid4(),
                tenant_id=t.id,
                entrada_padron_id=ep.id,
                materia_id=m.id,
                actividad="TP2",
                nota_textual="Aprobado",
                origen=OrigenCalificacionDB.IMPORTADO,
                creado_por=user.id,
            ),
        ]

        inserted = await repo.bulk_create(
            calificaciones=calificaciones,
            session=db_session,
        )
        assert len(inserted) == 2
        for c in inserted:
            assert c.id is not None

    async def test_lista_vacia_retorna_lista_vacia(
        self, db_session,
    ):
        repo = CalificacionRepository()
        result = await repo.bulk_create(
            calificaciones=[],
            session=db_session,
        )
        assert result == []


class TestSoftDeleteByMateriaYUsuario:
    """Grupo 5.5-5.6: soft_delete_by_materia_y_usuario."""

    async def test_marca_deleted_at_y_deleted_by(
        self, db_session, materia, version_padron, user_factory,
    ):
        t, m = materia
        _, ep = version_padron
        user = await user_factory(db_session, tenant_id=t.id)
        deleter_id = uuid.uuid4()
        repo = CalificacionRepository()

        c = Calificacion(
            id=uuid.uuid4(),
            tenant_id=t.id,
            entrada_padron_id=ep.id,
            materia_id=m.id,
            actividad="TP1",
            nota_numerica=80.0,
            origen=OrigenCalificacionDB.IMPORTADO,
            creado_por=user.id,
        )
        db_session.add(c)
        await db_session.commit()

        affected = await repo.soft_delete_by_materia_y_usuario(
            tenant_id=t.id,
            materia_id=m.id,
            creado_por=user.id,
            deleted_by=deleter_id,
            session=db_session,
        )
        assert affected == 1

        await db_session.refresh(c)
        assert c.deleted_at is not None
        assert c.deleted_by == deleter_id

    async def test_sin_registros_retorna_0(
        self, db_session, materia, user_factory,
    ):
        t, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        repo = CalificacionRepository()

        affected = await repo.soft_delete_by_materia_y_usuario(
            tenant_id=t.id,
            materia_id=m.id,
            creado_por=user.id,
            deleted_by=uuid.uuid4(),
            session=db_session,
        )
        assert affected == 0


class TestGetByEntradaPadron:
    """Grupo 5.7-5.8: get_by_entrada_padron."""

    async def test_devuelve_calificaciones_de_alumno(
        self, db_session, materia, version_padron, user_factory,
    ):
        t, m = materia
        vp, ep = version_padron
        user = await user_factory(db_session, tenant_id=t.id)
        repo = CalificacionRepository()

        c = Calificacion(
            id=uuid.uuid4(),
            tenant_id=t.id,
            entrada_padron_id=ep.id,
            materia_id=m.id,
            actividad="TP1",
            nota_numerica=80.0,
            origen=OrigenCalificacionDB.IMPORTADO,
            creado_por=user.id,
        )
        db_session.add(c)
        await db_session.commit()

        result = await repo.get_by_entrada_padron(
            tenant_id=t.id,
            entrada_padron_id=ep.id,
            materia_id=m.id,
            session=db_session,
        )
        assert len(result) == 1
        assert result[0].id == c.id

    async def test_retorna_lista_vacia_sin_calificaciones(
        self, db_session, version_padron,
    ):
        vp, ep = version_padron
        repo = CalificacionRepository()

        result = await repo.get_by_entrada_padron(
            tenant_id=vp.tenant_id,
            entrada_padron_id=ep.id,
            materia_id=uuid.uuid4(),
            session=db_session,
        )
        assert result == []


class TestIndicesRepository:
    """Test auxiliar: verifica que el repositorio usa índices correctos."""

    async def test_indices_existen(
        self, db_session,
    ):
        """Verifica que los índices compuestos existen en la BD."""
        from sqlalchemy import text

        result = await db_session.execute(
            text("SELECT indexname FROM pg_indexes WHERE tablename = 'calificacion'")
        )
        index_names = [r[0] for r in result.fetchall()]
        assert any("ix_calificacion_tenant_materia" in name for name in index_names)
        assert any("ix_calificacion_tenant_entrada" in name for name in index_names)
