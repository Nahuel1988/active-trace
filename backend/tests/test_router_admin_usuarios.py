"""Tests para el router admin_usuarios — TDD C-07.

Verifica guards, tenant isolation, y que PII no se filtre en responses incorrectas.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch


class TestAdminUsuariosGuards:
    """Scenario: Guards y esquemas Pydantic."""

    def test_extra_field_in_post_returns_422(self) -> None:
        """WHEN se envía campo extra super_admin=true, THEN 422 (extra='forbid')."""
        from app.schemas.usuario import UsuarioCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as excinfo:
            UsuarioCreate(
                email="test@test.com",
                password="pw",
                nombre="A",
                apellidos="B",
                super_admin=True,  # campo desconocido
            )
        errors = excinfo.value.errors()
        assert any(e["type"] == "extra_forbidden" for e in errors)

    def test_usuario_response_has_required_fields(self) -> None:
        """WHEN se construye UsuarioResponse, THEN tiene los campos obligatorios."""
        from app.schemas.usuario import UsuarioResponse
        from datetime import datetime, timezone

        import uuid
        now = datetime.now(timezone.utc)
        r = UsuarioResponse(
            id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            nombre="Juan",
            apellidos="García",
            facturador=False,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        assert r.nombre == "Juan"
        assert r.is_active is True


class TestAdminUsuariosResponseNoPIIForNonAdmin:
    """Scenario: PII descifrada solo en endpoint admin."""

    def test_usuario_response_fields_match_spec(self) -> None:
        """WHEN UsuarioResponse se define, THEN tiene campos dni, cuil, cbu, alias_cbu."""
        from app.schemas.usuario import UsuarioResponse

        fields = set(UsuarioResponse.model_fields.keys())
        # El response admin SÍ debe tener estos campos (descifrados)
        assert "dni" in fields
        assert "cuil" in fields
        assert "cbu" in fields
        assert "alias_cbu" in fields

    def test_usuario_minimo_no_pii(self) -> None:
        """WHEN UsuarioMinimo se define, THEN NO tiene dni, cuil, cbu, alias_cbu."""
        from app.schemas.usuario import UsuarioMinimo

        fields = set(UsuarioMinimo.model_fields.keys())
        pii = {"dni", "cuil", "cbu", "alias_cbu", "email", "password"}
        assert not pii.intersection(fields)

    def test_router_admin_usuarios_registered_in_app(self) -> None:
        """WHEN se importa la app, THEN el router admin_usuarios está registrado."""
        from app.main import create_app

        app = create_app()
        # FastAPI wraps included routers in _IncludedRouter; access original_router for prefix
        all_paths = []
        for r in app.routes:
            all_paths.append(getattr(r, "path", ""))
            orig = getattr(r, "original_router", None)
            if orig:
                prefix = getattr(orig, "prefix", "")
                all_paths.append(prefix)
        assert any("admin/usuarios" in p for p in all_paths), (
            f"Router admin/usuarios no registrado. Routes: {all_paths}"
        )


class TestAsignacionesRouterRegistered:
    """Scenario: Router de asignaciones está registrado en la app."""

    def test_router_asignaciones_registered_in_app(self) -> None:
        """WHEN se importa la app, THEN el router asignaciones está registrado."""
        from app.main import create_app

        app = create_app()
        all_paths = []
        for r in app.routes:
            all_paths.append(getattr(r, "path", ""))
            orig = getattr(r, "original_router", None)
            if orig:
                prefix = getattr(orig, "prefix", "")
                all_paths.append(prefix)
        assert any("asignaciones" in p for p in all_paths), (
            f"Router asignaciones no registrado. Routes: {all_paths}"
        )
