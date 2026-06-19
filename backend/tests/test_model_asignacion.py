"""Tests para el modelo Asignacion — TDD C-07.

RED: tests fallan porque el modelo Asignacion no existe.
GREEN: se crea el modelo y los tests pasan.
TRIANGULATE: FKs nullable, índices, estado_vigencia con 4 escenarios.
"""

import uuid
import pytest
from datetime import datetime, timezone, timedelta


class TestAsignacionModelColumns:
    """Scenario: Modelo Asignacion tiene todas las columnas esperadas."""

    def test_asignacion_model_importable(self) -> None:
        """WHEN se importa Asignacion, THEN no hay error."""
        from app.models.asignacion import Asignacion
        assert Asignacion is not None

    def test_asignacion_has_tenant_scoped_mixin_columns(self) -> None:
        """WHEN se inspecciona Asignacion, THEN tiene id, tenant_id, created_at, deleted_at."""
        from app.models.asignacion import Asignacion

        col_names = {c.name for c in Asignacion.__table__.columns}
        for col in ("id", "tenant_id", "created_at", "updated_at", "deleted_at"):
            assert col in col_names, f"Missing column: {col}"

    def test_asignacion_has_domain_columns(self) -> None:
        """WHEN se inspecciona Asignacion, THEN tiene columnas de dominio."""
        from app.models.asignacion import Asignacion

        col_names = {c.name for c in Asignacion.__table__.columns}
        for col in ("usuario_id", "role_id", "materia_id", "carrera_id",
                    "cohorte_id", "responsable_id", "desde", "hasta", "comisiones"):
            assert col in col_names, f"Missing domain column: {col}"

    def test_nullable_fk_columns(self) -> None:
        """WHEN se inspecciona Asignacion, THEN FKs de contexto académico son nullable."""
        from app.models.asignacion import Asignacion

        table_cols = {c.name: c for c in Asignacion.__table__.columns}
        for col_name in ("materia_id", "carrera_id", "cohorte_id", "responsable_id", "hasta"):
            col = table_cols[col_name]
            assert col.nullable is True, f"Column {col_name} should be nullable"

    def test_required_columns_are_not_nullable(self) -> None:
        """WHEN se inspecciona Asignacion, THEN usuario_id, role_id, tenant_id, desde son NOT NULL."""
        from app.models.asignacion import Asignacion

        table_cols = {c.name: c for c in Asignacion.__table__.columns}
        for col_name in ("usuario_id", "role_id", "tenant_id", "desde"):
            col = table_cols[col_name]
            assert col.nullable is False, f"Column {col_name} should NOT be nullable"


class TestAsignacionInstantiation:
    """Scenario: Asignacion puede instanciarse con distintas combinaciones."""

    def test_coordinador_minimal_instantiation(self) -> None:
        """WHEN se instancia Asignacion para COORDINADOR con sólo carrera_id, THEN válido."""
        from app.models.asignacion import Asignacion

        a = Asignacion(
            tenant_id=uuid.uuid4(),
            usuario_id=uuid.uuid4(),
            role_id=uuid.uuid4(),
            carrera_id=uuid.uuid4(),
            desde=datetime.now(timezone.utc),
        )
        assert a.materia_id is None
        assert a.cohorte_id is None
        assert a.responsable_id is None
        assert a.hasta is None

    def test_profesor_full_instantiation(self) -> None:
        """WHEN se instancia Asignacion para PROFESOR completo, THEN todos los campos."""
        from app.models.asignacion import Asignacion

        a = Asignacion(
            tenant_id=uuid.uuid4(),
            usuario_id=uuid.uuid4(),
            role_id=uuid.uuid4(),
            materia_id=uuid.uuid4(),
            carrera_id=uuid.uuid4(),
            cohorte_id=uuid.uuid4(),
            comisiones=["A1", "A2"],
            responsable_id=uuid.uuid4(),
            desde=datetime.now(timezone.utc),
            hasta=datetime(2027, 12, 31, tzinfo=timezone.utc),
        )
        assert a.comisiones == ["A1", "A2"]
        assert a.hasta is not None

    def test_repr_does_not_raise_with_null_fields(self) -> None:
        """WHEN se evalúa repr(asignacion) con campos NULL, THEN no lanza error."""
        from app.models.asignacion import Asignacion

        a = Asignacion(
            tenant_id=uuid.uuid4(),
            usuario_id=uuid.uuid4(),
            role_id=uuid.uuid4(),
            desde=datetime.now(timezone.utc),
        )
        # No debe lanzar excepción aunque muchos campos sean None
        r = repr(a)
        assert "Asignacion" in r


class TestAsignacionIndexes:
    """TRIANGULATE: índices declarados en __table_args__."""

    def test_index_tenant_usuario_exists(self) -> None:
        """WHEN se inspecciona la tabla asignacion, THEN ix_asignacion_tenant_usuario existe."""
        from app.models.asignacion import Asignacion

        index_names = {idx.name for idx in Asignacion.__table__.indexes}
        assert "ix_asignacion_tenant_usuario" in index_names, (
            f"Missing index ix_asignacion_tenant_usuario. Got: {index_names}"
        )

    def test_index_tenant_responsable_exists(self) -> None:
        """WHEN se inspecciona la tabla asignacion, THEN ix_asignacion_tenant_responsable existe."""
        from app.models.asignacion import Asignacion

        index_names = {idx.name for idx in Asignacion.__table__.indexes}
        assert "ix_asignacion_tenant_responsable" in index_names, (
            f"Missing index ix_asignacion_tenant_responsable. Got: {index_names}"
        )

    def test_index_tenant_deleted_exists(self) -> None:
        """WHEN se inspecciona la tabla asignacion, THEN ix_asignacion_tenant_deleted existe."""
        from app.models.asignacion import Asignacion

        index_names = {idx.name for idx in Asignacion.__table__.indexes}
        assert "ix_asignacion_tenant_deleted" in index_names, (
            f"Missing index ix_asignacion_tenant_deleted. Got: {index_names}"
        )


class TestAsignacionEstadoVigencia:
    """TRIANGULATE: 4 escenarios del spec asignacion-modelo para estado_vigencia."""

    def test_hasta_futuro_es_vigente(self) -> None:
        """WHEN hasta es futuro, THEN estado_vigencia es 'Vigente'."""
        from app.models.asignacion import Asignacion

        a = Asignacion(
            tenant_id=uuid.uuid4(),
            usuario_id=uuid.uuid4(),
            role_id=uuid.uuid4(),
            desde=datetime.now(timezone.utc) - timedelta(days=10),
            hasta=datetime.now(timezone.utc) + timedelta(days=30),
        )
        assert a.estado_vigencia == "Vigente"

    def test_hasta_null_es_vigente(self) -> None:
        """WHEN hasta es NULL y desde es pasado, THEN estado_vigencia es 'Vigente'."""
        from app.models.asignacion import Asignacion

        a = Asignacion(
            tenant_id=uuid.uuid4(),
            usuario_id=uuid.uuid4(),
            role_id=uuid.uuid4(),
            desde=datetime.now(timezone.utc) - timedelta(days=5),
            hasta=None,
        )
        assert a.estado_vigencia == "Vigente"

    def test_hasta_pasado_es_vencida(self) -> None:
        """WHEN hasta ya pasó, THEN estado_vigencia es 'Vencida'."""
        from app.models.asignacion import Asignacion

        a = Asignacion(
            tenant_id=uuid.uuid4(),
            usuario_id=uuid.uuid4(),
            role_id=uuid.uuid4(),
            desde=datetime.now(timezone.utc) - timedelta(days=30),
            hasta=datetime.now(timezone.utc) - timedelta(days=1),
        )
        assert a.estado_vigencia == "Vencida"

    def test_desde_futuro_es_vencida(self) -> None:
        """WHEN desde es futuro (no comenzada), THEN estado_vigencia es 'Vencida'."""
        from app.models.asignacion import Asignacion

        a = Asignacion(
            tenant_id=uuid.uuid4(),
            usuario_id=uuid.uuid4(),
            role_id=uuid.uuid4(),
            desde=datetime.now(timezone.utc) + timedelta(days=10),
            hasta=None,
        )
        assert a.estado_vigencia == "Vencida"
