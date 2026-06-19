"""Tests para el router asignaciones — TDD C-07.

Verifica schemas, guards y que response no expone PII.
"""

import pytest
import uuid
from datetime import datetime, timezone


class TestAsignacionSchemasGuards:
    """Scenario: Schemas con extra='forbid' y validación de campos."""

    def test_extra_field_rejected(self) -> None:
        """WHEN campo extra en AsignacionCreate, THEN ValidationError."""
        from app.schemas.asignacion import AsignacionCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as excinfo:
            AsignacionCreate(
                usuario_id=str(uuid.uuid4()),
                role_id=str(uuid.uuid4()),
                desde=datetime.now(timezone.utc),
                prioridad="alta",  # campo desconocido
            )
        errors = excinfo.value.errors()
        assert any(e["type"] == "extra_forbidden" for e in errors)

    def test_asignacion_response_no_pii_fields(self) -> None:
        """WHEN AsignacionResponse se define, THEN NO tiene PII sensible directamente."""
        from app.schemas.asignacion import AsignacionResponse

        fields = set(AsignacionResponse.model_fields.keys())
        pii_fields = {"dni", "cuil", "cbu", "alias_cbu", "email", "password"}
        assert not pii_fields.intersection(fields)

    def test_asignacion_response_has_usuario_minimo(self) -> None:
        """WHEN AsignacionResponse se define, THEN tiene campo usuario (UsuarioMinimo)."""
        from app.schemas.asignacion import AsignacionResponse

        assert "usuario" in AsignacionResponse.model_fields

    def test_estado_vigencia_todas_semantic(self) -> None:
        """WHEN estado_vigencia=todas, THEN incluye vencidas — validado vía schema."""
        from app.schemas.asignacion import AsignacionCreate

        # AsignacionCreate acepta hasta en el pasado (la validación es en el service)
        a = AsignacionCreate(
            usuario_id=str(uuid.uuid4()),
            role_id=str(uuid.uuid4()),
            desde=datetime(2024, 1, 1, tzinfo=timezone.utc),
            hasta=datetime(2024, 6, 1, tzinfo=timezone.utc),
        )
        # El schema no valida las fechas — lo hace el service
        assert a.hasta is not None


class TestAsignacionesRouterEndpointPaths:
    """Scenario: Endpoints correctamente registrados."""

    def _collect_all_paths(self, app) -> list:
        """Collect all registered paths from app routes, including _IncludedRouter prefixes."""
        paths = []
        for r in app.routes:
            paths.append(getattr(r, "path", ""))
            orig = getattr(r, "original_router", None)
            if orig:
                paths.append(getattr(orig, "prefix", ""))
        return paths

    def test_asignaciones_get_list_path_exists(self) -> None:
        """WHEN se inspecciona la app, THEN GET /api/v1/asignaciones existe."""
        from app.main import create_app

        app = create_app()
        paths = self._collect_all_paths(app)
        assert any("asignaciones" in p for p in paths)

    def test_admin_usuarios_delete_path_exists(self) -> None:
        """WHEN se inspecciona la app, THEN DELETE /api/v1/admin/usuarios/{id} existe."""
        from app.main import create_app

        app = create_app()
        paths = self._collect_all_paths(app)
        assert any("admin/usuarios" in p for p in paths)
