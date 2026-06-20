"""Integration tests — importación E2E (preview + confirm).

Strict TDD: RED → GREEN → TRIANGULATE → REFACTOR.
Usa contenedor de DB efímero — no mocks.
Marcado @pytest.mark.requires_db.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditCodes, AuditContext
from app.models.calificacion import Calificacion, OrigenCalificacionDB
from app.services.calificacion_service import CalificacionError, CalificacionService

pytestmark = pytest.mark.requires_db


def _build_audit_ctx(user, tenant_id) -> AuditContext:
    return AuditContext(
        actor_id=user.id,
        tenant_id=tenant_id,
        ip="127.0.0.1",
        user_agent="test",
    )


def _crear_csv_con_entrada_ids(
    entrada_ids: list[str],
    nombres: list[str],
    apellidos: list[str],
    actividades: list[str],
    filas: list[list[str]],
) -> bytes:
    """Crea CSV con columna entrada_padron_id, nombre, apellidos y actividades."""
    header = ["entrada_padron_id", "nombre", "apellidos"] + actividades
    lines = [",".join(header)]
    for i, row in enumerate(filas):
        lines.append(",".join([entrada_ids[i], nombres[i], apellidos[i]] + row))
    content = "\n".join(lines)
    return content.encode("utf-8-sig")


class TestImportE2E:
    """Preview + confirmar importación E2E (Task 14.2)."""

    async def test_preview_y_confirmar_carga_completa(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        version_padron,
        cohorte,
    ):
        """14.2 RED: subir .csv → preview → confirm → 201 con calificaciones creadas."""
        t, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        vp, ep = version_padron  # EntradaPadron del fixture
        audit_ctx = _build_audit_ctx(user, t.id)

        # Segundo alumno
        from app.models.padron import EntradaPadron

        ep2 = EntradaPadron(
            id=uuid.uuid4(),
            tenant_id=t.id,
            version_padron_id=vp.id,
            nombre="María",
            apellidos="García",
            email_encrypted="cifrado:test2",
            comision="A",
        )
        db_session.add(ep2)
        await db_session.commit()
        await db_session.refresh(ep2)

        service = CalificacionService()
        contenido = _crear_csv_con_entrada_ids(
            entrada_ids=[str(ep.id), str(ep2.id)],
            nombres=["Juan", "María"],
            apellidos=["Pérez", "García"],
            actividades=["Parcial (Real)", "TP (Real)", "Estado"],
            filas=[
                ["85", "90", "Aprobado"],
                ["70", "65", "Regular"],
            ],
        )

        # PREVIEW
        preview = await service.preview_archivo(contenido, "notas.csv")
        assert preview.total_filas == 2
        assert len(preview.columnas_detectadas) >= 3
        assert preview.errores == []

        # CONFIRMAR con archivo_parseado completo
        # (preview.muestra_primeras_3 NO incluye entrada_padron_id porque
        #  esa columna está en COLUMNAS_IGNORADAS. Usamos filas completas.)
        filas_parseadas = [
            {"entrada_padron_id": str(ep.id), "Parcial (Real)": "85", "TP (Real)": "90", "Estado": "Aprobado"},
            {"entrada_padron_id": str(ep2.id), "Parcial (Real)": "70", "TP (Real)": "65", "Estado": "Regular"},
        ]
        columnas = [
            {"nombre": "entrada_padron_id", "tipo": "ignorada"},
            {"nombre": "Parcial (Real)", "tipo": "numerica"},
            {"nombre": "TP (Real)", "tipo": "numerica"},
            {"nombre": "Estado", "tipo": "textual"},
        ]
        total = await service.confirmar_importacion(
            tenant_id=t.id,
            materia_id=m.id,
            archivo_parseado=filas_parseadas,
            columnas_detectadas=columnas,
            actividades_seleccionadas=["Parcial (Real)", "TP (Real)"],
            actor_id=user.id,
            audit_ctx=audit_ctx,
            session=db_session,
        )

        assert total == 4  # 2 alumnos × 2 actividades

        # Verificar en DB
        stmt = (
            select(Calificacion)
            .where(
                Calificacion.tenant_id == t.id,
                Calificacion.materia_id == m.id,
                Calificacion.creado_por == user.id,
                Calificacion.deleted_at.is_(None),
            )
        )
        result = await db_session.execute(stmt)
        califs = result.scalars().all()
        assert len(califs) == 4
        for c in califs:
            assert c.origen == OrigenCalificacionDB.IMPORTADO
            assert c.creado_por == user.id
            assert c.deleted_at is None

    async def test_preview_archivo_formato_invalido_422(
        self,
    ):
        """14.2 TRIANGULATE: formato no soportado → error 422."""
        service = CalificacionService()
        contenido = b"nombre,apellidos,nota\nJuan,Perez,7"

        preview = await service.preview_archivo(contenido, "notas.txt")
        assert len(preview.errores) >= 1
        assert "no soportado" in preview.errores[0].lower()

    async def test_confirmar_actividad_inexistente_422(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
    ):
        """14.2 TRIANGULATE: actividad seleccionada no existe en columnas → 422."""
        t, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        audit_ctx = _build_audit_ctx(user, t.id)

        service = CalificacionService()
        filas = [{"entrada_padron_id": str(uuid.uuid4()), "Parcial (Real)": "85"}]
        columnas = [{"nombre": "Parcial (Real)", "tipo": "numerica"}]

        with pytest.raises(CalificacionError) as exc:
            await service.confirmar_importacion(
                tenant_id=t.id,
                materia_id=m.id,
                archivo_parseado=filas,
                columnas_detectadas=columnas,
                actividades_seleccionadas=["ActividadInexistente"],
                actor_id=user.id,
                audit_ctx=audit_ctx,
                session=db_session,
            )
        assert exc.value.status_code == 422
        assert "ActividadInexistente" in exc.value.detail

    async def test_confirmar_max_filas_excedido_413(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
    ):
        """14.2 TRIANGULATE: más de MAX_CALIFICACIONES_IMPORT → 413."""
        import os
        t, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        audit_ctx = _build_audit_ctx(user, t.id)

        max_rows = int(os.getenv("MAX_CALIFICACIONES_IMPORT", "5000"))

        # Crear muchas filas para exceder el límite
        # 2501 filas × 2 actividades = 5002 > 5000
        filas_muchas = [
            {"entrada_padron_id": str(uuid.uuid4()), "Act1 (Real)": "70", "Act2 (Real)": "80"}
            for _ in range(max_rows // 2 + 2)
        ]
        columnas = [
            {"nombre": "Act1 (Real)", "tipo": "numerica"},
            {"nombre": "Act2 (Real)", "tipo": "numerica"},
        ]

        service = CalificacionService()
        with pytest.raises(CalificacionError) as exc:
            await service.confirmar_importacion(
                tenant_id=t.id,
                materia_id=m.id,
                archivo_parseado=filas_muchas,
                columnas_detectadas=columnas,
                actividades_seleccionadas=["Act1 (Real)", "Act2 (Real)"],
                actor_id=user.id,
                audit_ctx=audit_ctx,
                session=db_session,
            )
        assert exc.value.status_code == 413

    async def test_import_con_notas_numericas_y_textuales(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        version_padron,
    ):
        """14.2 TRIANGULATE: importación mezcla notas numéricas y textuales."""
        t, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        vp, ep = version_padron
        audit_ctx = _build_audit_ctx(user, t.id)

        service = CalificacionService()
        filas = [{
            "entrada_padron_id": str(ep.id),
            "Parcial (Real)": "85",
            "Estado": "Aprobado",
        }]
        columnas = [
            {"nombre": "entrada_padron_id", "tipo": "ignorada"},
            {"nombre": "Parcial (Real)", "tipo": "numerica"},
            {"nombre": "Estado", "tipo": "textual"},
        ]

        total = await service.confirmar_importacion(
            tenant_id=t.id,
            materia_id=m.id,
            archivo_parseado=filas,
            columnas_detectadas=columnas,
            actividades_seleccionadas=["Parcial (Real)", "Estado"],
            actor_id=user.id,
            audit_ctx=audit_ctx,
            session=db_session,
        )
        assert total == 2

        # Verificar que una es numérica y otra textual
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
        assert len(califs) == 2

        numerica = [c for c in califs if c.nota_numerica is not None]
        textual = [c for c in califs if c.nota_textual is not None]
        assert len(numerica) == 1
        assert len(textual) == 1
        assert numerica[0].nota_numerica == 85
        assert textual[0].nota_textual == "Aprobado"

    async def test_import_sin_datos_422(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
    ):
        """14.2 TRIANGULATE: confirmar sin datos (celdas vacías) → 422."""
        t, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        audit_ctx = _build_audit_ctx(user, t.id)

        service = CalificacionService()
        filas = [{"entrada_padron_id": str(uuid.uuid4()), "Nota (Real)": ""}]
        columnas = [{"nombre": "Nota (Real)", "tipo": "numerica"}]

        with pytest.raises(CalificacionError) as exc:
            await service.confirmar_importacion(
                tenant_id=t.id,
                materia_id=m.id,
                archivo_parseado=filas,
                columnas_detectadas=columnas,
                actividades_seleccionadas=["Nota (Real)"],
                actor_id=user.id,
                audit_ctx=audit_ctx,
                session=db_session,
            )
        assert exc.value.status_code == 422
