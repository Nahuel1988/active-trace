"""Tests para migración 006 — usuarios_y_asignaciones — TDD C-07.

Verifica que la migración aplica y revierte correctamente.
Requiere DB real (--run-db).
"""

import pytest

pytestmark = pytest.mark.requires_db


class TestMigration006Upgrade:
    """Scenario: alembic upgrade 006 crea columnas, tabla e índices esperados."""

    async def test_migration_adds_user_pii_columns(self, db_session) -> None:
        """WHEN se ejecuta upgrade 006, THEN user tiene las 10 columnas nuevas."""
        from sqlalchemy import text

        result = await db_session.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'user'
                AND column_name IN (
                    'nombre', 'apellidos', 'dni_encrypted', 'cuil_encrypted',
                    'cbu_encrypted', 'alias_cbu_encrypted', 'banco', 'regional',
                    'legajo_profesional', 'facturador'
                )
            """)
        )
        cols = {row[0] for row in result}
        expected = {
            "nombre", "apellidos", "dni_encrypted", "cuil_encrypted",
            "cbu_encrypted", "alias_cbu_encrypted", "banco", "regional",
            "legajo_profesional", "facturador"
        }
        assert expected.issubset(cols), f"Missing columns: {expected - cols}"

    async def test_migration_creates_asignacion_table(self, db_session) -> None:
        """WHEN se ejecuta upgrade 006, THEN tabla asignacion existe."""
        from sqlalchemy import text

        result = await db_session.execute(
            text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'asignacion'
            """)
        )
        tables = [row[0] for row in result]
        assert "asignacion" in tables

    async def test_migration_creates_asignacion_indexes(self, db_session) -> None:
        """WHEN se ejecuta upgrade 006, THEN existen los 3 índices de asignacion."""
        from sqlalchemy import text

        result = await db_session.execute(
            text("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'asignacion'
            """)
        )
        index_names = {row[0] for row in result}
        expected = {
            "ix_asignacion_tenant_usuario",
            "ix_asignacion_tenant_responsable",
            "ix_asignacion_tenant_deleted",
        }
        assert expected.issubset(index_names), f"Missing indexes: {expected - index_names}"


class TestMigration006Tables:
    """Scenario: tabla asignacion tiene las columnas y constraints correctas."""

    async def test_asignacion_has_required_columns(self, db_session) -> None:
        """WHEN asignacion existe, THEN tiene todas las columnas esperadas."""
        from sqlalchemy import text

        result = await db_session.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'asignacion'
            """)
        )
        cols = {row[0] for row in result}
        expected = {
            "id", "tenant_id", "created_at", "updated_at", "deleted_at",
            "usuario_id", "role_id", "materia_id", "carrera_id", "cohorte_id",
            "responsable_id", "comisiones", "desde", "hasta"
        }
        assert expected.issubset(cols), f"Missing columns: {expected - cols}"

    async def test_facturador_has_false_default(self, db_session) -> None:
        """WHEN se inspecciona user.facturador, THEN tiene server_default false."""
        from sqlalchemy import text

        result = await db_session.execute(
            text("""
                SELECT column_default
                FROM information_schema.columns
                WHERE table_name = 'user'
                AND column_name = 'facturador'
            """)
        )
        row = result.fetchone()
        assert row is not None
        default = row[0]
        assert default is not None and "false" in str(default).lower()
