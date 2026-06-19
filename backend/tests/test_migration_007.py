"""Tests para migración 007 — perfil_y_mensajeria — TDD C-20.

Verifica que la migración aplica correctamente:
    - Columna modalidad_cobro en user
    - Tablas hilo_mensaje y mensaje_interno con índices de aislamiento

Requiere DB real (--run-db).
"""

import pytest

pytestmark = pytest.mark.requires_db


class TestMigration007UserModalidadCobro:
    """12.1 RED: migración 007 agrega modalidad_cobro a user."""

    async def test_user_has_modalidad_cobro_column(self, db_session) -> None:
        """WHEN upgrade 007, THEN user tiene columna modalidad_cobro."""
        from sqlalchemy import text

        result = await db_session.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'user'
                AND column_name = 'modalidad_cobro'
            """)
        )
        cols = [row[0] for row in result]
        assert "modalidad_cobro" in cols, "modalidad_cobro missing from user table"

    async def test_modalidad_cobro_is_nullable(self, db_session) -> None:
        """WHEN modalidad_cobro existe, THEN es nullable (convivencia con pre-existentes)."""
        from sqlalchemy import text

        result = await db_session.execute(
            text("""
                SELECT is_nullable
                FROM information_schema.columns
                WHERE table_name = 'user'
                AND column_name = 'modalidad_cobro'
            """)
        )
        row = result.fetchone()
        assert row is not None
        assert row[0] == "YES"


class TestMigration007HiloMensaje:
    """12.1 RED: tabla hilo_mensaje existe con columnas y índices correctos."""

    async def test_hilo_mensaje_table_exists(self, db_session) -> None:
        """WHEN upgrade 007, THEN tabla hilo_mensaje existe."""
        from sqlalchemy import text

        result = await db_session.execute(
            text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'hilo_mensaje'
            """)
        )
        tables = [row[0] for row in result]
        assert "hilo_mensaje" in tables

    async def test_hilo_mensaje_has_required_columns(self, db_session) -> None:
        """WHEN hilo_mensaje existe, THEN tiene todas las columnas esperadas."""
        from sqlalchemy import text

        result = await db_session.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'hilo_mensaje'
            """)
        )
        cols = {row[0] for row in result}
        expected = {
            "id", "tenant_id", "created_at", "updated_at", "deleted_at",
            "asunto", "iniciado_por", "destinatario_id",
        }
        assert expected.issubset(cols), f"Missing: {expected - cols}"

    async def test_hilo_mensaje_has_tenant_destinatario_index(self, db_session) -> None:
        """WHEN hilo_mensaje existe, THEN índice (tenant_id, destinatario_id) presente."""
        from sqlalchemy import text

        result = await db_session.execute(
            text("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'hilo_mensaje'
            """)
        )
        indexes = {row[0] for row in result}
        assert any("destinatario" in idx for idx in indexes), (
            f"No destinatario index found. Indexes: {indexes}"
        )


class TestMigration007MensajeInterno:
    """12.1 RED: tabla mensaje_interno existe con columnas y índices correctos."""

    async def test_mensaje_interno_table_exists(self, db_session) -> None:
        """WHEN upgrade 007, THEN tabla mensaje_interno existe."""
        from sqlalchemy import text

        result = await db_session.execute(
            text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'mensaje_interno'
            """)
        )
        tables = [row[0] for row in result]
        assert "mensaje_interno" in tables

    async def test_mensaje_interno_has_required_columns(self, db_session) -> None:
        """WHEN mensaje_interno existe, THEN tiene todas las columnas esperadas."""
        from sqlalchemy import text

        result = await db_session.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'mensaje_interno'
            """)
        )
        cols = {row[0] for row in result}
        expected = {
            "id", "tenant_id", "created_at", "updated_at", "deleted_at",
            "hilo_id", "autor_id", "cuerpo", "creado_at", "leido_at",
        }
        assert expected.issubset(cols), f"Missing: {expected - cols}"

    async def test_mensaje_interno_has_hilo_index(self, db_session) -> None:
        """WHEN mensaje_interno existe, THEN índice (tenant_id, hilo_id) presente."""
        from sqlalchemy import text

        result = await db_session.execute(
            text("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'mensaje_interno'
            """)
        )
        indexes = {row[0] for row in result}
        assert any("hilo" in idx for idx in indexes), (
            f"No hilo index found. Indexes: {indexes}"
        )
