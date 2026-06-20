"""Integration tests — reporte de finalización (RN-08).

Strict TDD: RED → GREEN → TRIANGULATE → REFACTOR.
Usa contenedor de DB efímero — no mocks.
Marcado @pytest.mark.requires_db.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calificacion import Calificacion, OrigenCalificacionDB
from app.services.calificacion_service import CalificacionService

pytestmark = pytest.mark.requires_db


def _crear_csv_reporte(
    entrada_ids: list[str],
    nombres: list[str],
    apellidos: list[str],
    columnas_textuales: list[str],
    filas: list[list[str]],
) -> bytes:
    """Crea un CSV tipo reporte de finalización."""
    header = ["entrada_padron_id", "nombre", "apellidos"] + columnas_textuales
    lines = [",".join(header)]
    for i in range(len(entrada_ids)):
        row = [entrada_ids[i], nombres[i], apellidos[i]] + filas[i]
        lines.append(",".join(row))
    content = "\n".join(lines)
    return content.encode("utf-8-sig")


class TestReporteFinalizacion:
    """Reporte de entregas finalizadas sin calificar (Task 14.4)."""

    async def test_reporte_detecta_entregas_sin_calificar(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        version_padron,
    ):
        """14.4 RED: reporte detecta actividades textuales finalizadas sin calificar."""
        t, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        vp, ep = version_padron

        # Segunda entrada en el padrón
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

        # Crear una calificación existente para ep (actividad "Estado")
        calif = Calificacion(
            id=uuid.uuid4(),
            tenant_id=t.id,
            entrada_padron_id=ep.id,
            materia_id=m.id,
            actividad="Estado",
            nota_textual="Aprobado",
            origen=OrigenCalificacionDB.IMPORTADO,
            creado_por=user.id,
        )
        db_session.add(calif)
        await db_session.commit()

        # CSV con columna textual "Estado" y numérica "Parcial (Real)"
        contenido = _crear_csv_reporte(
            entrada_ids=[str(ep.id), str(ep2.id)],
            nombres=["Juan", "María"],
            apellidos=["Pérez", "García"],
            columnas_textuales=["Estado", "Observaciones"],
            filas=[
                ["Aprobado", "Buen trabajo"],   # Juan: Estado ya calificado
                ["Regular", "Entregó tarde"],    # María: ninguna calificada
            ],
        )

        service = CalificacionService()
        reporte = await service.reporte_finalizacion(
            tenant_id=t.id,
            materia_id=m.id,
            archivo_contenido=contenido,
            nombre_archivo="finalizacion.csv",
            session=db_session,
        )

        # Juan tiene "Estado" calificado → solo "Observaciones" aparece
        # María no tiene nada calificado → ambas aparecen
        assert len(reporte.items) >= 1

        items_maria = [i for i in reporte.items if "María" in i.alumno]
        assert len(items_maria) == 2  # Estado + Observaciones sin calificar

        items_juan = [i for i in reporte.items if "Juan" in i.alumno]
        assert len(items_juan) >= 1
        # "Estado" de Juan ya está calificado → no aparece
        actividades_juan = {i.actividad for i in items_juan}
        assert "Estado" not in actividades_juan

    async def test_reporte_todo_calificado_lista_vacia(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        version_padron,
    ):
        """14.4 TRIANGULATE: todas las actividades ya calificadas → lista vacía."""
        t, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        vp, ep = version_padron

        # Calificar todas las actividades textuales
        for actividad in ["Estado", "Observaciones"]:
            c = Calificacion(
                id=uuid.uuid4(),
                tenant_id=t.id,
                entrada_padron_id=ep.id,
                materia_id=m.id,
                actividad=actividad,
                nota_textual="Aprobado",
                origen=OrigenCalificacionDB.IMPORTADO,
                creado_por=user.id,
            )
            db_session.add(c)
        await db_session.commit()

        contenido = _crear_csv_reporte(
            entrada_ids=[str(ep.id)],
            nombres=["Juan"],
            apellidos=["Pérez"],
            columnas_textuales=["Estado", "Observaciones"],
            filas=[["Aprobado", "Buen trabajo"]],
        )

        service = CalificacionService()
        reporte = await service.reporte_finalizacion(
            tenant_id=t.id,
            materia_id=m.id,
            archivo_contenido=contenido,
            nombre_archivo="finalizacion.csv",
            session=db_session,
        )
        assert len(reporte.items) == 0

    async def test_reporte_solo_actividades_textuales_RN08(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        version_padron,
    ):
        """14.4 TRIANGULATE: solo actividades textuales en reporte (RN-08)."""
        t, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        vp, ep = version_padron

        # CSV con actividad numérica "(Real)" y textual
        header = ["entrada_padron_id", "nombre", "apellidos", "Parcial (Real)", "Estado"]
        lines = [
            ",".join(header),
            f"{ep.id},Juan,Pérez,85,Aprobado",
        ]
        contenido = "\n".join(lines).encode("utf-8-sig")

        service = CalificacionService()
        reporte = await service.reporte_finalizacion(
            tenant_id=t.id,
            materia_id=m.id,
            archivo_contenido=contenido,
            nombre_archivo="finalizacion.csv",
            session=db_session,
        )

        # Solo "Estado" (textual) debería aparecer, no "Parcial (Real)"
        actividades = {i.actividad for i in reporte.items}
        assert "Estado" in actividades
        assert "Parcial (Real)" not in actividades

    async def test_reporte_sin_calificaciones_previas(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        version_padron,
    ):
        """14.4 TRIANGULATE: sin calificaciones previas → todas aparecen."""
        t, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        vp, ep = version_padron

        contenido = _crear_csv_reporte(
            entrada_ids=[str(ep.id)],
            nombres=["Juan"],
            apellidos=["Pérez"],
            columnas_textuales=["Estado", "Observaciones"],
            filas=[["Aprobado", "Buen trabajo"]],
        )

        service = CalificacionService()
        reporte = await service.reporte_finalizacion(
            tenant_id=t.id,
            materia_id=m.id,
            archivo_contenido=contenido,
            nombre_archivo="finalizacion.csv",
            session=db_session,
        )

        assert len(reporte.items) == 2  # Ambas actividades sin calificar

    async def test_reporte_archivo_vacio_retorna_vacio(
        self,
        db_session: AsyncSession,
        materia,
    ):
        """14.4 TRIANGULATE: archivo vacío → lista vacía."""
        t, m = materia
        contenido = b""

        service = CalificacionService()
        reporte = await service.reporte_finalizacion(
            tenant_id=t.id,
            materia_id=m.id,
            archivo_contenido=contenido,
            nombre_archivo="finalizacion.csv",
            session=db_session,
        )
        assert len(reporte.items) == 0

    async def test_reporte_sin_entrada_ids(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
    ):
        """14.4 TRIANGULATE: archivo sin columna entrada_padron_id → vacío."""
        t, m = materia

        header = ["nombre", "apellidos", "Estado"]
        lines = [",".join(header), "Juan,Pérez,Aprobado"]
        contenido = "\n".join(lines).encode("utf-8-sig")

        service = CalificacionService()
        reporte = await service.reporte_finalizacion(
            tenant_id=t.id,
            materia_id=m.id,
            archivo_contenido=contenido,
            nombre_archivo="finalizacion.csv",
            session=db_session,
        )
        assert len(reporte.items) == 0
