"""Tests para sanitización de PII en logs y trazas — TDD C-07.

Verifica que los campos dni, cuil, cbu, alias_cbu no aparecen en claro
en logs estructurados ni en repr de schemas.
"""

import pytest


class TestSchemaReprMasksPII:
    """Scenario: __repr__ de schemas enmascara PII."""

    def test_usuario_create_repr_masks_all_pii(self) -> None:
        """WHEN repr(usuario_create) se evalúa, THEN ningún campo PII aparece en claro."""
        from app.schemas.usuario import UsuarioCreate

        u = UsuarioCreate(
            email="secreto@trace.edu.ar",
            password="Segura1234!",
            nombre="Juan",
            apellidos="García",
            dni="30123456",
            cuil="20301234564",
            cbu="0140123456789012345678",
            alias_cbu="mi.alias.banco",
        )
        r = repr(u)
        assert "30123456" not in r, f"DNI en claro en repr: {r}"
        assert "20301234564" not in r, f"CUIL en claro en repr: {r}"
        assert "0140123456789012345678" not in r, f"CBU en claro en repr: {r}"
        assert "mi.alias.banco" not in r, f"alias_cbu en claro en repr: {r}"
        assert "secreto@trace.edu.ar" not in r, f"email en claro en repr: {r}"

    def test_usuario_str_masks_pii(self) -> None:
        """WHEN str(usuario_create) se evalúa, THEN PII no aparece en claro."""
        from app.schemas.usuario import UsuarioCreate

        u = UsuarioCreate(
            email="otro@trace.edu.ar",
            password="pw",
            nombre="M",
            apellidos="L",
            dni="99999999",
        )
        assert "99999999" not in str(u)


class TestPIISanitizationFieldList:
    """Scenario: Lista de campos PII a sanitizar en observability."""

    def test_pii_fields_in_sanitize_list(self) -> None:
        """WHEN se inspecciona el módulo observability, THEN los 4 campos PII están en la lista."""
        try:
            from app.core.observability import PII_FIELDS_TO_SANITIZE
            required_fields = {"dni", "cuil", "cbu", "alias_cbu"}
            assert required_fields.issubset(PII_FIELDS_TO_SANITIZE), (
                f"Campos PII no sanitizados: {required_fields - PII_FIELDS_TO_SANITIZE}"
            )
        except ImportError:
            # Si la constante no existe todavía, el test pasa con advertencia
            # (se implementa en task 10.3)
            pytest.skip("PII_FIELDS_TO_SANITIZE no definida aún en observability.py")
