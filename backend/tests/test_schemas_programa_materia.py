"""Tests for ProgramaMateria Pydantic schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.programa_materia import (
    ProgramaMateriaCreate,
    ProgramaMateriaUpdate,
    ProgramaMateriaResponse,
)


class TestProgramaMateriaCreate:
    def test_valid_create(self):
        data = {
            "materia_id": "123e4567-e89b-12d3-a456-426614174000",
            "carrera_id": "223e4567-e89b-12d3-a456-426614174001",
            "cohorte_id": "323e4567-e89b-12d3-a456-426614174002",
            "titulo": "Programa de Álgebra",
            "referencia_archivo": "storage://tenant-a/programas/prog-2026.pdf",
        }
        obj = ProgramaMateriaCreate(**data)
        assert obj.titulo == "Programa de Álgebra"
        assert obj.referencia_archivo == "storage://tenant-a/programas/prog-2026.pdf"

    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            ProgramaMateriaCreate(
                materia_id="123e4567-e89b-12d3-a456-426614174000",
                carrera_id="223e4567-e89b-12d3-a456-426614174001",
                cohorte_id="323e4567-e89b-12d3-a456-426614174002",
                titulo="Test",
                extra_field="no",
            )

    def test_referencia_archivo_opaco_string(self):
        """referencia_archivo se acepta como string opaco sin validar formato."""
        data = {
            "materia_id": "123e4567-e89b-12d3-a456-426614174000",
            "carrera_id": "223e4567-e89b-12d3-a456-426614174001",
            "cohorte_id": "323e4567-e89b-12d3-a456-426614174002",
            "titulo": "Test",
            "referencia_archivo": "cualquier-string-opaco-sin-formato",
        }
        obj = ProgramaMateriaCreate(**data)
        assert obj.referencia_archivo == "cualquier-string-opaco-sin-formato"

    def test_referencia_archivo_opcional(self):
        data = {
            "materia_id": "123e4567-e89b-12d3-a456-426614174000",
            "carrera_id": "223e4567-e89b-12d3-a456-426614174001",
            "cohorte_id": "323e4567-e89b-12d3-a456-426614174002",
            "titulo": "Test",
        }
        obj = ProgramaMateriaCreate(**data)
        assert obj.referencia_archivo is None


class TestProgramaMateriaUpdate:
    def test_valid_update(self):
        obj = ProgramaMateriaUpdate(titulo="Nuevo título", referencia_archivo="nueva-ref")
        assert obj.titulo == "Nuevo título"
        assert obj.referencia_archivo == "nueva-ref"

    def test_partial_update(self):
        obj = ProgramaMateriaUpdate(titulo="Solo título")
        assert obj.titulo == "Solo título"
        assert obj.referencia_archivo is None

    def test_empty_update(self):
        obj = ProgramaMateriaUpdate()
        assert obj.titulo is None
        assert obj.referencia_archivo is None

    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            ProgramaMateriaUpdate(titulo="Test", invalid="no")


class TestProgramaMateriaResponse:
    def test_from_attributes(self):
        data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "tenant_id": "223e4567-e89b-12d3-a456-426614174001",
            "materia_id": "323e4567-e89b-12d3-a456-426614174002",
            "carrera_id": "423e4567-e89b-12d3-a456-426614174003",
            "cohorte_id": "523e4567-e89b-12d3-a456-426614174004",
            "titulo": "Programa",
            "referencia_archivo": "ref",
            "cargado_at": "2026-01-01T00:00:00Z",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
        obj = ProgramaMateriaResponse(**data)
        assert obj.id == data["id"]
        assert obj.titulo == "Programa"

    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            ProgramaMateriaResponse(
                id="1", tenant_id="1", materia_id="1", carrera_id="1",
                cohorte_id="1", titulo="T", cargado_at="2026-01-01T00:00:00Z",
                created_at="2026-01-01T00:00:00Z", updated_at="2026-01-01T00:00:00Z",
                invalid="no",
            )
