"""Tests Pydantic v2 schemas para el módulo de calificaciones (C-10).

Strict TDD: RED → GREEN → TRIANGULATE → REFACTOR.
Todos los schemas deben usar ``extra='forbid'`` (regla dura R5).
"""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from app.schemas.calificacion import (
    CalificacionCreate,
    CalificacionResponse,
    ConfirmarImportRequest,
    OrigenCalificacion,
    PreviewResponse,
    ReporteFinalizacionItem,
    ReporteFinalizacionResponse,
    UmbralMateriaCreate,
    UmbralMateriaResponse,
    VaciarRequest,
)


class TestOrigenCalificacion:
    def test_valores_enum(self):
        assert OrigenCalificacion.IMPORTADO.value == "importado"
        assert OrigenCalificacion.MANUAL.value == "manual"


class TestCalificacionCreate:
    """RED: test que CalificacionCreate rechaza campos extra,
    acepta nota_numerica nullable y nota_textual nullable,
    pero rechaza ambos nulos."""

    def test_minimal_valido(self):
        uid = uuid.uuid4()
        data = {
            "entrada_padron_id": str(uid),
            "materia_id": str(uid),
            "actividad": "TP1",
            "nota_numerica": 8.5,
        }
        c = CalificacionCreate(**data)
        assert c.entrada_padron_id == uid
        assert c.materia_id == uid
        assert c.actividad == "TP1"
        assert c.nota_numerica == 8.5
        assert c.nota_textual is None
        assert c.origen == OrigenCalificacion.IMPORTADO

    def test_nota_textual_valida(self):
        uid = uuid.uuid4()
        data = {
            "entrada_padron_id": str(uid),
            "materia_id": str(uid),
            "actividad": "TP1",
            "nota_textual": "Satisfactorio",
        }
        c = CalificacionCreate(**data)
        assert c.nota_textual == "Satisfactorio"
        assert c.nota_numerica is None

    def test_ambas_notas_nulas_rechazado(self):
        uid = uuid.uuid4()
        with pytest.raises(ValidationError, match="al menos una nota"):
            CalificacionCreate(
                entrada_padron_id=uid,
                materia_id=uid,
                actividad="TP1",
            )

    def test_extra_field_forbidden(self):
        uid = uuid.uuid4()
        with pytest.raises(ValidationError):
            CalificacionCreate(
                entrada_padron_id=uid,
                materia_id=uid,
                actividad="TP1",
                nota_numerica=7.0,
                extra="no",
            )

    def test_origen_explicito(self):
        uid = uuid.uuid4()
        data = {
            "entrada_padron_id": str(uid),
            "materia_id": str(uid),
            "actividad": "TP1",
            "nota_numerica": 9.0,
            "origen": "manual",
        }
        c = CalificacionCreate(**data)
        assert c.origen == OrigenCalificacion.MANUAL


class TestPreviewResponse:
    def test_valido(self):
        r = PreviewResponse(
            columnas_detectadas=[
                {"nombre": "Apellido y Nombre", "tipo": "ignorada"},
                {"nombre": "TP1 (Real)", "tipo": "numerica"},
                {"nombre": "TP2", "tipo": "textual"},
            ],
            total_filas=30,
            muestra_primeras_3=[
                {"Apellido y Nombre": "Pérez, Juan", "TP1 (Real)": "8", "TP2": "Satisfactorio"},
                {"Apellido y Nombre": "García, María", "TP1 (Real)": "6", "TP2": "Supera lo esperado"},
                {"Apellido y Nombre": "López, Pedro", "TP1 (Real)": "4", "TP2": "En proceso"},
            ],
            errores=[],
        )
        assert r.total_filas == 30
        assert len(r.columnas_detectadas) == 3

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            PreviewResponse(
                columnas_detectadas=[],
                total_filas=0,
                muestra_primeras_3=[],
                errores=[],
                extra="no",
            )

    def test_con_errores(self):
        r = PreviewResponse(
            columnas_detectadas=[],
            total_filas=0,
            muestra_primeras_3=[],
            errores=["Archivo vacío"],
        )
        assert len(r.errores) == 1


class TestConfirmarImportRequest:
    def test_valido(self):
        uid = uuid.uuid4()
        data = {
            "materia_id": str(uid),
            "actividades_seleccionadas": ["TP1 (Real)", "TP2"],
        }
        r = ConfirmarImportRequest(**data)
        assert r.materia_id == uid
        assert r.actividades_seleccionadas == ["TP1 (Real)", "TP2"]

    def test_extra_field_forbidden(self):
        uid = uuid.uuid4()
        with pytest.raises(ValidationError):
            ConfirmarImportRequest(
                materia_id=uid,
                actividades_seleccionadas=[],
                extra="no",
            )

    def test_actividades_vacia(self):
        uid = uuid.uuid4()
        r = ConfirmarImportRequest(
            materia_id=uid,
            actividades_seleccionadas=[],
        )
        assert r.actividades_seleccionadas == []


class TestCalificacionResponse:
    """RED: CalificacionResponse incluye campo aprobado derivado."""

    def test_valido(self):
        now = "2025-06-01T00:00:00Z"
        uid = uuid.uuid4()
        r = CalificacionResponse(
            id=uid,
            entrada_padron_id=uid,
            materia_id=uid,
            actividad="TP1",
            nota_numerica=8.0,
            nota_textual=None,
            aprobado=True,
            origen="importado",
            creado_por=uid,
            creada_at=now,
        )
        assert r.aprobado is True
        assert r.nota_numerica == 8.0

    def test_con_nota_textual(self):
        uid = uuid.uuid4()
        r = CalificacionResponse(
            id=uid,
            entrada_padron_id=uid,
            materia_id=uid,
            actividad="TP1",
            nota_numerica=None,
            nota_textual="Satisfactorio",
            aprobado=True,
            origen="importado",
            creado_por=uid,
            creada_at="2025-06-01T00:00:00Z",
        )
        assert r.aprobado is True
        assert r.nota_textual == "Satisfactorio"

    def test_extra_field_forbidden(self):
        uid = uuid.uuid4()
        with pytest.raises(ValidationError):
            CalificacionResponse(
                id=uid,
                entrada_padron_id=uid,
                materia_id=uid,
                actividad="TP1",
                aprobado=True,
                origen="importado",
                creado_por=uid,
                creada_at="2025-06-01T00:00:00Z",
                extra="no",
            )


class TestUmbralMateriaCreate:
    def test_valido(self):
        data = {
            "umbral_pct": 70,
            "valores_aprobatorios": ["Satisfactorio", "Supera lo esperado"],
        }
        u = UmbralMateriaCreate(**data)
        assert u.umbral_pct == 70
        assert u.valores_aprobatorios == ["Satisfactorio", "Supera lo esperado"]

    def test_valores_aprobatorios_opcional(self):
        u = UmbralMateriaCreate(umbral_pct=60)
        assert u.valores_aprobatorios is None

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            UmbralMateriaCreate(umbral_pct=60, extra="no")

    def test_umbral_fuera_rango_menor(self):
        with pytest.raises(ValidationError):
            UmbralMateriaCreate(umbral_pct=-1)

    def test_umbral_fuera_rango_mayor(self):
        with pytest.raises(ValidationError):
            UmbralMateriaCreate(umbral_pct=101)

    def test_umbral_en_borde(self):
        u0 = UmbralMateriaCreate(umbral_pct=0)
        assert u0.umbral_pct == 0
        u100 = UmbralMateriaCreate(umbral_pct=100)
        assert u100.umbral_pct == 100


class TestUmbralMateriaResponse:
    def test_valido(self):
        uid = uuid.uuid4()
        r = UmbralMateriaResponse(
            id=uid,
            asignacion_id=uid,
            materia_id=uid,
            umbral_pct=70,
            valores_aprobatorios=["Satisfactorio"],
        )
        assert r.umbral_pct == 70

    def test_extra_field_forbidden(self):
        uid = uuid.uuid4()
        with pytest.raises(ValidationError):
            UmbralMateriaResponse(
                id=uid,
                asignacion_id=uid,
                materia_id=uid,
                umbral_pct=60,
                extra="no",
            )


class TestReporteFinalizacionItem:
    def test_valido(self):
        uid = uuid.uuid4()
        item = ReporteFinalizacionItem(
            entrada_padron_id=uid,
            alumno="Pérez, Juan",
            actividad="TP2",
            fecha_finalizacion="2025-06-01",
        )
        assert item.alumno == "Pérez, Juan"

    def test_extra_field_forbidden(self):
        uid = uuid.uuid4()
        with pytest.raises(ValidationError):
            ReporteFinalizacionItem(
                entrada_padron_id=uid,
                alumno="Juan",
                actividad="TP1",
                fecha_finalizacion="2025-06-01",
                extra="no",
            )


class TestReporteFinalizacionResponse:
    def test_valido(self):
        uid = uuid.uuid4()
        r = ReporteFinalizacionResponse(
            items=[
                ReporteFinalizacionItem(
                    entrada_padron_id=uid,
                    alumno="Pérez, Juan",
                    actividad="TP2",
                    fecha_finalizacion="2025-06-01",
                )
            ]
        )
        assert len(r.items) == 1

    def test_lista_vacia(self):
        r = ReporteFinalizacionResponse(items=[])
        assert r.items == []


class TestVaciarRequest:
    def test_valido(self):
        uid = uuid.uuid4()
        r = VaciarRequest(materia_id=uid)
        assert r.materia_id == uid

    def test_extra_field_forbidden(self):
        uid = uuid.uuid4()
        with pytest.raises(ValidationError):
            VaciarRequest(materia_id=uid, extra="no")
