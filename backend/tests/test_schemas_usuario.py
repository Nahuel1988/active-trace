"""Tests para Pydantic schemas de Usuario — TDD C-07.

RED: tests fallan porque los schemas no existen.
GREEN: se crean los schemas y los tests pasan.
TRIANGULATE: __repr__ enmascara PII, from_orm descifra correctamente.
"""

import pytest
from pydantic import ValidationError


class TestUsuarioCreateHappyPath:
    """Scenario: Validación happy path de UsuarioCreate."""

    def test_usuario_create_minimal_valid(self) -> None:
        """WHEN se instancia UsuarioCreate con campos mínimos, THEN es válido."""
        from app.schemas.usuario import UsuarioCreate

        u = UsuarioCreate(
            email="docente@trace.edu.ar",
            password="Segura1234!",
            nombre="Juan",
            apellidos="García",
        )
        assert u.email == "docente@trace.edu.ar"
        assert u.nombre == "Juan"
        assert u.apellidos == "García"

    def test_usuario_create_full_with_pii(self) -> None:
        """WHEN se instancia UsuarioCreate con todos los campos PII, THEN es válido."""
        from app.schemas.usuario import UsuarioCreate

        u = UsuarioCreate(
            email="docente@trace.edu.ar",
            password="Segura1234!",
            nombre="Juan",
            apellidos="García",
            dni="30123456",
            cuil="20301234564",
            cbu="0140123456789012345678",
            alias_cbu="mi.alias.banco",
            banco="Banco Provincia",
            regional="Mendoza",
            legajo="LEG-001",
            legajo_profesional="LP-100",
            facturador=True,
        )
        assert u.dni == "30123456"
        assert u.cuil == "20301234564"
        assert u.cbu == "0140123456789012345678"
        assert u.facturador is True

    def test_usuario_create_extra_field_rejected(self) -> None:
        """WHEN se pasa campo desconocido, THEN ValidationError (extra='forbid')."""
        from app.schemas.usuario import UsuarioCreate

        with pytest.raises(ValidationError) as excinfo:
            UsuarioCreate(
                email="docente@trace.edu.ar",
                password="Segura1234!",
                nombre="Juan",
                apellidos="García",
                super_admin=True,  # campo desconocido
            )
        errors = excinfo.value.errors()
        assert any(e["type"] == "extra_forbidden" for e in errors)

    def test_usuario_create_facturador_defaults_false(self) -> None:
        """WHEN facturador no se especifica, THEN default es False."""
        from app.schemas.usuario import UsuarioCreate

        u = UsuarioCreate(
            email="docente@trace.edu.ar",
            password="Segura1234!",
            nombre="Juan",
            apellidos="García",
        )
        assert u.facturador is False


class TestUsuarioUpdateHappyPath:
    """Scenario: Validación happy path de UsuarioUpdate (todos opcionales)."""

    def test_usuario_update_empty_is_valid(self) -> None:
        """WHEN se instancia UsuarioUpdate vacío, THEN es válido (todos opcionales)."""
        from app.schemas.usuario import UsuarioUpdate

        u = UsuarioUpdate()
        assert u.nombre is None
        assert u.apellidos is None

    def test_usuario_update_partial(self) -> None:
        """WHEN se actualizan solo regional y facturador, THEN es válido."""
        from app.schemas.usuario import UsuarioUpdate

        u = UsuarioUpdate(regional="Córdoba", facturador=True)
        assert u.regional == "Córdoba"
        assert u.facturador is True
        assert u.nombre is None

    def test_usuario_update_extra_field_rejected(self) -> None:
        """WHEN se pasa campo desconocido en update, THEN ValidationError."""
        from app.schemas.usuario import UsuarioUpdate

        with pytest.raises(ValidationError) as excinfo:
            UsuarioUpdate(campo_extra="valor")
        errors = excinfo.value.errors()
        assert any(e["type"] == "extra_forbidden" for e in errors)


class TestUsuarioResponseHappyPath:
    """Scenario: UsuarioResponse acepta campos de la DB."""

    def test_usuario_response_from_dict(self) -> None:
        """WHEN se instancia UsuarioResponse con campos completos, THEN es válido."""
        import uuid
        from datetime import datetime, timezone

        from app.schemas.usuario import UsuarioResponse

        now = datetime.now(timezone.utc)
        r = UsuarioResponse(
            id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            email="docente@trace.edu.ar",
            nombre="Juan",
            apellidos="García",
            legajo="LEG-001",
            legajo_profesional=None,
            banco=None,
            regional=None,
            dni=None,
            cuil=None,
            cbu=None,
            alias_cbu=None,
            facturador=False,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        assert r.nombre == "Juan"
        assert r.facturador is False


class TestUsuarioReprMasksPII:
    """TRIANGULATE: __repr__ enmascara campos PII."""

    def test_repr_masks_dni(self) -> None:
        """WHEN repr(usuario_create) se evalúa, THEN dni NO aparece en claro."""
        from app.schemas.usuario import UsuarioCreate

        u = UsuarioCreate(
            email="docente@trace.edu.ar",
            password="Segura1234!",
            nombre="Juan",
            apellidos="García",
            dni="30123456",
        )
        representation = repr(u)
        assert "30123456" not in representation

    def test_repr_masks_cuil(self) -> None:
        """WHEN repr(usuario_create) se evalúa, THEN cuil NO aparece en claro."""
        from app.schemas.usuario import UsuarioCreate

        u = UsuarioCreate(
            email="docente@trace.edu.ar",
            password="Segura1234!",
            nombre="Juan",
            apellidos="García",
            cuil="20301234564",
        )
        representation = repr(u)
        assert "20301234564" not in representation

    def test_repr_masks_cbu(self) -> None:
        """WHEN repr(usuario_create) se evalúa, THEN cbu NO aparece en claro."""
        from app.schemas.usuario import UsuarioCreate

        u = UsuarioCreate(
            email="docente@trace.edu.ar",
            password="Segura1234!",
            nombre="Juan",
            apellidos="García",
            cbu="0140123456789012345678",
        )
        representation = repr(u)
        assert "0140123456789012345678" not in representation

    def test_repr_masks_alias_cbu(self) -> None:
        """WHEN repr(usuario_create) se evalúa, THEN alias_cbu NO aparece en claro."""
        from app.schemas.usuario import UsuarioCreate

        u = UsuarioCreate(
            email="docente@trace.edu.ar",
            password="Segura1234!",
            nombre="Juan",
            apellidos="García",
            alias_cbu="mi.alias.banco",
        )
        representation = repr(u)
        assert "mi.alias.banco" not in representation

    def test_repr_masks_email(self) -> None:
        """WHEN repr(usuario_create) se evalúa, THEN email NO aparece en claro."""
        from app.schemas.usuario import UsuarioCreate

        u = UsuarioCreate(
            email="secreto@trace.edu.ar",
            password="Segura1234!",
            nombre="Juan",
            apellidos="García",
        )
        representation = repr(u)
        assert "secreto@trace.edu.ar" not in representation
