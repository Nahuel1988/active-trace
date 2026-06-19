"""Tests para migration 002_auth — creación de las 6 tablas de auth.

Verifica que `alembic upgrade head` (desde 001 → 002) cree las tablas
y que `alembic downgrade -1` las elimine correctamente en orden inverso
de dependencias.

Usa subprocess para invocar alembic sobre la base de test.
Requiere PostgreSQL corriendo (--run-db).
"""

import subprocess
import sys
from pathlib import Path

import pytest
import asyncpg

BACKEND_DIR = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.requires_db

# Lista de tablas que debe crear la migración 002
AUTH_TABLES = [
    "role",
    "user",
    "password_reset_token",
    "refresh_token",
    "totp_secret",
    "user_role",
]

DATABASE_URL = "postgresql://activia:activia@localhost:5432/activia_trace_test"


def _alembic(*args: str) -> str:
    """Ejecuta alembic como módulo Python y retorna stdout+stderr."""
    result = subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        capture_output=True,
        text=True,
        cwd=str(BACKEND_DIR),
    )
    if result.returncode != 0:
        msg = f"alembic {' '.join(args)} failed\nstdout:{result.stdout}\nstderr:{result.stderr}"
        raise RuntimeError(msg)
    return result.stdout + result.stderr


async def _get_tables() -> list[str]:
    """Retorna lista de tablas públicas en la base de test."""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        rows = await conn.fetch(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' ORDER BY table_name"
        )
        return [r["table_name"] for r in rows]
    finally:
        await conn.close()


async def _get_alembic_version() -> str | None:
    """Retorna la versión actual de alembic en la base."""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        row = await conn.fetchrow("SELECT version_num FROM alembic_version")
        return row["version_num"] if row else None
    finally:
        await conn.close()


async def _drop_all_auth_tables():
    """Borra las 6 tablas de auth si existen (para reset entre tests)."""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        for table in reversed(AUTH_TABLES):
            await conn.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
    finally:
        await conn.close()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
async def reset_to_001():
    """Fixture que asegura que arrancamos en migration 001 (solo tenant).

    Si estamos en head (002), hace downgrade -1.
    Si estamos en 001, no hace nada.
    """
    version = await _get_alembic_version()
    if version is None:
        # Sin version → aplicar 001 primero
        _alembic("upgrade", "ce9effa4bfdd")
    elif version != "ce9effa4bfdd":
        # Estamos en 002 o superior → downgrade
        _alembic("downgrade", "ce9effa4bfdd")
    # También limpiamos tablas residuales por si acaso
    await _drop_all_auth_tables()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestMigration002Upgrade:
    """Scenario: Aplicar migration 002 desde 001."""

    async def test_upgrade_creates_all_auth_tables(self):
        """WHEN corremos upgrade head, THEN las 6 tablas de auth existen."""
        _alembic("upgrade", "head")

        tables = await _get_tables()
        for table in AUTH_TABLES:
            assert table in tables, f"Tabla '{table}' no fue creada por migration 002"

    async def test_upgrade_sets_alembic_version(self):
        """WHEN upgrade a 002, THEN alembic_version apunta a 002."""
        _alembic("upgrade", "87ff312e2a56")

        version = await _get_alembic_version()
        assert version is not None
        assert version == "87ff312e2a56"

    async def test_upgrade_key_constraints_exist(self):
        """WHEN upgrade head, THEN cada tabla tiene sus constraints.

        Verifica PK, FKs y UNIQUE esperados.
        """
        _alembic("upgrade", "head")

        conn = await asyncpg.connect(DATABASE_URL)
        try:
            # Helper: decodifica contype que asyncpg retorna como bytes
            def _t(rows):
                return {r["contype"].decode() if isinstance(r["contype"], bytes) else r["contype"] for r in rows}

            def _fk_count(rows):
                """Cuenta FKs decodificando contype."""
                return sum(
                    1 for r in rows
                    if (r["contype"].decode() if isinstance(r["contype"], bytes) else r["contype"]) == "f"
                )

            # --- user: PK, FK tenant, UNIQUE(tenant_id, email_lookup)
            user_con = await conn.fetch(
                "SELECT conname, contype FROM pg_catalog.pg_constraint "
                "WHERE conrelid = 'user'::regclass ORDER BY contype"
            )
            user_types = _t(user_con)
            assert "p" in user_types, "user PK missing"
            assert "f" in user_types, "user FK missing"
            assert "u" in user_types, "user UNIQUE missing"

            # --- role: PK, FK tenant, UNIQUE(tenant_id, code)
            role_con = await conn.fetch(
                "SELECT conname, contype FROM pg_catalog.pg_constraint "
                "WHERE conrelid = 'role'::regclass ORDER BY contype"
            )
            role_types = _t(role_con)
            assert "p" in role_types
            assert "f" in role_types
            assert "u" in role_types

            # --- user_role: PK compuesta, FKs
            ur_con = await conn.fetch(
                "SELECT conname, contype FROM pg_catalog.pg_constraint "
                "WHERE conrelid = 'user_role'::regclass ORDER BY contype"
            )
            ur_types = _t(ur_con)
            assert "p" in ur_types, "user_role PK missing"
            # user_role debería tener 3 FKs (user, role, tenant)
            assert _fk_count(ur_con) == 3, f"user_role esperaba 3 FKs"

            # --- refresh_token: PK, FK tenant, FK user, UNIQUE token_hash
            rt_con = await conn.fetch(
                "SELECT conname, contype FROM pg_catalog.pg_constraint "
                "WHERE conrelid = 'refresh_token'::regclass ORDER BY contype"
            )
            rt_types = _t(rt_con)
            assert "p" in rt_types
            assert "u" in rt_types
            assert _fk_count(rt_con) == 2, f"refresh_token esperaba 2 FKs"

            # --- totp_secret: PK, FK tenant, FK user, UNIQUE user_id
            ts_con = await conn.fetch(
                "SELECT conname, contype FROM pg_catalog.pg_constraint "
                "WHERE conrelid = 'totp_secret'::regclass ORDER BY contype"
            )
            ts_types = _t(ts_con)
            assert "p" in ts_types
            assert "u" in ts_types
            assert _fk_count(ts_con) == 2, f"totp_secret esperaba 2 FKs"

            # --- password_reset_token: PK, FK tenant, FK user, UNIQUE token_hash
            prt_con = await conn.fetch(
                "SELECT conname, contype FROM pg_catalog.pg_constraint "
                "WHERE conrelid = 'password_reset_token'::regclass ORDER BY contype"
            )
            prt_types = _t(prt_con)
            assert "p" in prt_types
            assert "u" in prt_types
            assert _fk_count(prt_con) == 2, f"password_reset_token esperaba 2 FKs"
        finally:
            await conn.close()


class TestMigration002Downgrade:
    """Scenario: Revertir migration 002 desde 002 a 001."""

    async def test_downgrade_removes_all_auth_tables(self):
        """GIVEN migration 002 aplicada, WHEN downgrade a 001, THEN tablas eliminadas."""
        _alembic("upgrade", "87ff312e2a56")
        _alembic("downgrade", "ce9effa4bfdd")

        tables = await _get_tables()
        for table in AUTH_TABLES:
            assert table not in tables, f"Tabla '{table}' no fue eliminada por downgrade"

    async def test_downgrade_keeps_tenant_table(self):
        """WHEN downgrade a 001, THEN tabla tenant y alembic_version persisten."""
        _alembic("upgrade", "87ff312e2a56")
        _alembic("downgrade", "ce9effa4bfdd")

        tables = await _get_tables()
        assert "tenant" in tables, "Tenant table debe persistir tras downgrade"
        assert "alembic_version" in tables, "alembic_version debe persistir"

    async def test_downgrade_sets_version_to_001(self):
        """WHEN downgrade a 001, THEN alembic_version vuelve a 001."""
        _alembic("upgrade", "87ff312e2a56")
        _alembic("downgrade", "ce9effa4bfdd")

        version = await _get_alembic_version()
        assert version == "ce9effa4bfdd"

    async def test_downgrade_reapply_upgrade_is_idempotent(self):
        """GIVEN upgrade → downgrade → upgrade, THEN todo funciona de nuevo."""
        _alembic("upgrade", "87ff312e2a56")
        _alembic("downgrade", "ce9effa4bfdd")
        _alembic("upgrade", "87ff312e2a56")

        tables = await _get_tables()
        for table in AUTH_TABLES:
            assert table in tables, f"Tabla '{table}' no recreada tras re-upgrade"

        version = await _get_alembic_version()
        assert version == "87ff312e2a56"
