"""Tests para Pydantic schemas de Asignacion — TDD C-07.

RED: tests fallan porque los schemas no existen.
GREEN: se crean los schemas y los tests pasan.
TRIANGULATE: AsignacionResponse NO contiene PII sensible.
"""

import pytest
import uuid
from datetime import datetime, timezone
from pydantic import ValidationError


class TestAsignacionCreateHappyPath:
    """Scenario: Validación happy path de AsignacionCreate."""

    def test_asignacion_create_minimal_coordinador(self) -> None:
        """WHEN se crea AsignacionCreate para COORDINADOR con carrera_id, THEN válido."""
        from app.schemas.asignacion import AsignacionCreate

        a = AsignacionCreate(
            usuario_id=str(uuid.uuid4()),
            role_id=str(uuid.uuid4()),
            carrera_id=str(uuid.uuid4()),
            desde=datetime.now(timezone.utc),
        )
        assert a.materia_id is None
        assert a.cohorte_id is None
        assert a.comisiones == []

    def test_asignacion_create_full_profesor(self) -> None:
        """WHEN se crea AsignacionCreate para PROFESOR completo, THEN válido."""
        from app.schemas.asignacion import AsignacionCreate

        hasta = datetime(2027, 12, 31, tzinfo=timezone.utc)
        a = AsignacionCreate(
            usuario_id=str(uuid.uuid4()),
            role_id=str(uuid.uuid4()),
            materia_id=str(uuid.uuid4()),
            carrera_id=str(uuid.uuid4()),
            cohorte_id=str(uuid.uuid4()),
            comisiones=["A1", "A2"],
            responsable_id=str(uuid.uuid4()),
            desde=datetime.now(timezone.utc),
            hasta=hasta,
        )
        assert a.comisiones == ["A1", "A2"]
        assert a.hasta == hasta

    def test_asignacion_create_extra_field_rejected(self) -> None:
        """WHEN se pasa campo extra, THEN ValidationError (extra='forbid')."""
        from app.schemas.asignacion import AsignacionCreate

        with pytest.raises(ValidationError) as excinfo:
            AsignacionCreate(
                usuario_id=str(uuid.uuid4()),
                role_id=str(uuid.uuid4()),
                desde=datetime.now(timezone.utc),
                prioridad="alta",  # campo desconocido
            )
        errors = excinfo.value.errors()
        assert any(e["type"] == "extra_forbidden" for e in errors)


class TestAsignacionUpdateHappyPath:
    """Scenario: Validación happy path de AsignacionUpdate."""

    def test_asignacion_update_empty_valid(self) -> None:
        """WHEN AsignacionUpdate vacío, THEN válido (todos opcionales)."""
        from app.schemas.asignacion import AsignacionUpdate

        u = AsignacionUpdate()
        assert u.hasta is None
        assert u.responsable_id is None

    def test_asignacion_update_extra_rejected(self) -> None:
        """WHEN campo extra en update, THEN ValidationError."""
        from app.schemas.asignacion import AsignacionUpdate

        with pytest.raises(ValidationError) as excinfo:
            AsignacionUpdate(campo_raro=123)
        errors = excinfo.value.errors()
        assert any(e["type"] == "extra_forbidden" for e in errors)


class TestAsignacionResponseNoPII:
    """TRIANGULATE: AsignacionResponse NO contiene PII sensible del usuario."""

    def test_response_has_usuario_minimo(self) -> None:
        """WHEN se instancia AsignacionResponse, THEN sub-objeto usuario es UsuarioMinimo."""
        from app.schemas.asignacion import AsignacionResponse
        from app.schemas.usuario import UsuarioMinimo

        now = datetime.now(timezone.utc)
        r = AsignacionResponse(
            id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            usuario_id=str(uuid.uuid4()),
            role_id=str(uuid.uuid4()),
            materia_id=None,
            carrera_id=str(uuid.uuid4()),
            cohorte_id=None,
            comisiones=[],
            responsable_id=None,
            desde=now,
            hasta=None,
            estado_vigencia="Vigente",
            usuario=UsuarioMinimo(
                id=str(uuid.uuid4()),
                nombre="Juan",
                apellidos="García",
                legajo="LEG-001",
            ),
            created_at=now,
            updated_at=now,
        )
        assert r.usuario.nombre == "Juan"

    def test_response_no_pii_fields(self) -> None:
        """WHEN se obtiene AsignacionResponse, THEN NO contiene dni, cuil, cbu, alias_cbu, email."""
        from app.schemas.asignacion import AsignacionResponse

        response_fields = set(AsignacionResponse.model_fields.keys())
        pii_fields = {"dni", "cuil", "cbu", "alias_cbu", "email"}
        # Ningún campo PII debe estar en AsignacionResponse directamente
        assert not pii_fields.intersection(response_fields), (
            f"AsignacionResponse expone PII: {pii_fields.intersection(response_fields)}"
        )

    def test_usuario_minimo_no_pii_fields(self) -> None:
        """WHEN se obtiene UsuarioMinimo, THEN NO contiene campos PII."""
        from app.schemas.usuario import UsuarioMinimo

        fields = set(UsuarioMinimo.model_fields.keys())
        pii_fields = {"dni", "cuil", "cbu", "alias_cbu", "email", "password"}
        assert not pii_fields.intersection(fields), (
            f"UsuarioMinimo expone PII: {pii_fields.intersection(fields)}"
        )

    def test_response_extra_field_rejected(self) -> None:
        """WHEN campo extra en AsignacionCreate, THEN ValidationError."""
        from app.schemas.asignacion import AsignacionCreate

        with pytest.raises(ValidationError):
            AsignacionCreate(
                usuario_id=str(uuid.uuid4()),
                role_id=str(uuid.uuid4()),
                desde=datetime.now(timezone.utc),
                campo_desconocido="X",
            )
