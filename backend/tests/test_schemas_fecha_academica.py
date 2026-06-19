"""Tests for FechaAcademica Pydantic schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.fecha_academica import (
    FechaAcademicaCreate,
    FechaAcademicaUpdate,
    FechaAcademicaResponse,
    CalendarioPeriodo,
)


class TestFechaAcademicaCreate:
    def test_valid_create(self):
        data = {
            "materia_id": "123e4567-e89b-12d3-a456-426614174000",
            "cohorte_id": "223e4567-e89b-12d3-a456-426614174001",
            "tipo": "Parcial",
            "numero": 1,
            "periodo": "2026-1",
            "fecha": "2026-04-15T10:00:00Z",
            "titulo": "Primer Parcial",
        }
        obj = FechaAcademicaCreate(**data)
        assert obj.tipo == "Parcial"
        assert obj.numero == 1

    def test_tipo_fuera_del_enum_rejected(self):
        with pytest.raises(ValidationError):
            FechaAcademicaCreate(
                materia_id="1", cohorte_id="1", tipo="Examen",
                numero=1, periodo="2026-1", fecha="2026-04-15T10:00:00Z",
                titulo="Test",
            )

    def test_numero_cero_rejected(self):
        with pytest.raises(ValidationError):
            FechaAcademicaCreate(
                materia_id="1", cohorte_id="1", tipo="Parcial",
                numero=0, periodo="2026-1", fecha="2026-04-15T10:00:00Z",
                titulo="Test",
            )

    def test_numero_negativo_rejected(self):
        with pytest.raises(ValidationError):
            FechaAcademicaCreate(
                materia_id="1", cohorte_id="1", tipo="Parcial",
                numero=-1, periodo="2026-1", fecha="2026-04-15T10:00:00Z",
                titulo="Test",
            )

    def test_enums_validos_aceptados(self):
        for tipo in ("Parcial", "TP", "Coloquio", "Recuperatorio"):
            obj = FechaAcademicaCreate(
                materia_id="1", cohorte_id="1", tipo=tipo,
                numero=1, periodo="2026-1", fecha="2026-04-15T10:00:00Z",
                titulo="Test",
            )
            assert obj.tipo == tipo

    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            FechaAcademicaCreate(
                materia_id="1", cohorte_id="1", tipo="Parcial",
                numero=1, periodo="2026-1", fecha="2026-04-15T10:00:00Z",
                titulo="Test", extra="no",
            )


class TestFechaAcademicaUpdate:
    def test_valid_update(self):
        obj = FechaAcademicaUpdate(periodo="2026-2", fecha="2026-05-15T10:00:00Z")
        assert obj.periodo == "2026-2"

    def test_partial_update(self):
        obj = FechaAcademicaUpdate(titulo="Solo título")
        assert obj.titulo == "Solo título"
        assert obj.periodo is None

    def test_empty_update(self):
        obj = FechaAcademicaUpdate()
        assert obj.periodo is None
        assert obj.fecha is None
        assert obj.titulo is None

    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            FechaAcademicaUpdate(periodo="2026-1", invalid="no")


class TestFechaAcademicaResponse:
    def test_from_attributes(self):
        data = {
            "id": "1", "tenant_id": "1", "materia_id": "1", "cohorte_id": "1",
            "tipo": "Parcial", "numero": 1, "periodo": "2026-1",
            "fecha": "2026-04-15T10:00:00Z", "titulo": "Test",
            "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z",
        }
        obj = FechaAcademicaResponse(**data)
        assert obj.tipo == "Parcial"
        assert obj.numero == 1

    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            FechaAcademicaResponse(
                id="1", tenant_id="1", materia_id="1", cohorte_id="1",
                tipo="Parcial", numero=1, periodo="2026-1",
                fecha="2026-04-15T10:00:00Z", titulo="Test",
                created_at="2026-01-01T00:00:00Z", updated_at="2026-01-01T00:00:00Z",
                invalid="no",
            )


class TestCalendarioPeriodo:
    def test_valid(self):
        obj = CalendarioPeriodo(periodo="2026-1", fechas=[])
        assert obj.periodo == "2026-1"
        assert obj.fechas == []

    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            CalendarioPeriodo(periodo="2026-1", fechas=[], extra="no")
