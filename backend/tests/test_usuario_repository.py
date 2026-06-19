"""Tests para UsuarioRepository — TDD C-07.

RED: tests fallan porque el repositorio no existe.
GREEN: se crea el repositorio y los tests pasan.
TRIANGULATE: tenant isolation, soft delete, cifrado round-trip PII.

Require DB real (--run-db).
"""

import uuid
import pytest
from datetime import datetime, timezone

pytestmark = pytest.mark.requires_db


class TestUsuarioRepositoryCreate:
    """Scenario: Crear usuario con PII cifrada."""

    async def test_create_user_happy_path(self, db_session, tenant_factory) -> None:
        """WHEN se crea un usuario, THEN persiste con UUID y tenant_id."""
        from app.repositories.usuario_repository import UsuarioRepository
        from app.models.user import User

        tenant = await tenant_factory()
        repo = UsuarioRepository()

        user = await repo.create(
            tenant_id=tenant.id,
            email="docente@test.edu.ar",
            password_plain="Segura1234!",
            nombre="Juan",
            apellidos="García",
            session=db_session,
        )

        assert user.id is not None
        assert user.tenant_id == tenant.id
        assert user.nombre == "Juan"
        assert user.email_encrypted is not None
        assert "docente@test.edu.ar" not in user.email_encrypted

    async def test_create_user_with_pii_encrypts_fields(self, db_session, tenant_factory) -> None:
        """WHEN se crea usuario con DNI, THEN dni_encrypted no contiene el DNI en claro."""
        from app.repositories.usuario_repository import UsuarioRepository

        tenant = await tenant_factory()
        repo = UsuarioRepository()

        user = await repo.create(
            tenant_id=tenant.id,
            email=f"pii-test-{uuid.uuid4().hex[:6]}@test.edu.ar",
            password_plain="Segura1234!",
            nombre="María",
            apellidos="López",
            dni="30123456",
            cuil="20301234564",
            cbu="0140123456789012345678",
            alias_cbu="mi.alias.banco",
            session=db_session,
        )

        # Ciphertext no debe contener el valor en claro
        assert user.dni_encrypted is not None
        assert "30123456" not in user.dni_encrypted
        assert user.cuil_encrypted is not None
        assert "20301234564" not in user.cuil_encrypted
        assert user.cbu_encrypted is not None
        assert "0140123456789012345678" not in user.cbu_encrypted


class TestUsuarioRepositoryGetByEmailLookup:
    """Scenario: Búsqueda por email_lookup."""

    async def test_get_by_email_lookup_finds_user(self, db_session, tenant_factory) -> None:
        """WHEN se busca por email en mismo tenant, THEN retorna el usuario."""
        from app.repositories.usuario_repository import UsuarioRepository

        tenant = await tenant_factory()
        repo = UsuarioRepository()
        email = f"lookup-{uuid.uuid4().hex[:6]}@test.edu.ar"

        await repo.create(
            tenant_id=tenant.id,
            email=email,
            password_plain="Segura1234!",
            nombre="Test",
            apellidos="User",
            session=db_session,
        )

        found = await repo.get_by_email_lookup(
            email=email, tenant_id=tenant.id, session=db_session
        )
        assert found is not None
        assert found.tenant_id == tenant.id

    async def test_get_by_email_lookup_other_tenant_returns_none(
        self, db_session, tenant_factory
    ) -> None:
        """WHEN se busca en otro tenant, THEN retorna None (tenant isolation)."""
        from app.repositories.usuario_repository import UsuarioRepository

        tenant_a = await tenant_factory(slug=f"ta-{uuid.uuid4().hex[:6]}")
        tenant_b = await tenant_factory(slug=f"tb-{uuid.uuid4().hex[:6]}")
        repo = UsuarioRepository()
        email = f"iso-{uuid.uuid4().hex[:6]}@test.edu.ar"

        await repo.create(
            tenant_id=tenant_a.id,
            email=email,
            password_plain="Segura1234!",
            nombre="Test",
            apellidos="A",
            session=db_session,
        )

        found = await repo.get_by_email_lookup(
            email=email, tenant_id=tenant_b.id, session=db_session
        )
        assert found is None


class TestUsuarioRepositoryList:
    """Scenario: list filtra por tenant y excluye soft-deleted."""

    async def test_list_filters_by_tenant(self, db_session, tenant_factory) -> None:
        """WHEN se listan usuarios, THEN solo aparecen del tenant correcto."""
        from app.repositories.usuario_repository import UsuarioRepository

        tenant_a = await tenant_factory(slug=f"la-{uuid.uuid4().hex[:6]}")
        tenant_b = await tenant_factory(slug=f"lb-{uuid.uuid4().hex[:6]}")
        repo = UsuarioRepository()

        await repo.create(
            tenant_id=tenant_a.id,
            email=f"a-{uuid.uuid4().hex[:6]}@test.edu.ar",
            password_plain="pw",
            nombre="A",
            apellidos="A",
            session=db_session,
        )
        await repo.create(
            tenant_id=tenant_b.id,
            email=f"b-{uuid.uuid4().hex[:6]}@test.edu.ar",
            password_plain="pw",
            nombre="B",
            apellidos="B",
            session=db_session,
        )

        users_a = await repo.list(tenant_id=tenant_a.id, session=db_session)
        tenant_ids_a = {str(u.tenant_id) for u in users_a}
        assert all(t == str(tenant_a.id) for t in tenant_ids_a)


class TestUsuarioRepositorySoftDelete:
    """Scenario: soft delete preserva el registro."""

    async def test_soft_delete_does_not_destroy_data(self, db_session, tenant_factory) -> None:
        """WHEN se soft-deletea un usuario, THEN el registro persiste con deleted_at."""
        from app.repositories.usuario_repository import UsuarioRepository
        from sqlalchemy import select, text
        from app.models.user import User

        tenant = await tenant_factory()
        repo = UsuarioRepository()

        user = await repo.create(
            tenant_id=tenant.id,
            email=f"del-{uuid.uuid4().hex[:6]}@test.edu.ar",
            password_plain="pw",
            nombre="Delete",
            apellidos="Test",
            session=db_session,
        )
        user_id = user.id

        result = await repo.soft_delete(
            id=user_id, tenant_id=tenant.id, session=db_session
        )
        assert result is True

        # El usuario ya no aparece via get() (excluye soft-deleted)
        found = await repo.get(id=user_id, tenant_id=tenant.id, session=db_session)
        assert found is None

        # Pero sigue en la BD con deleted_at seteado
        stmt = select(User).where(User.id == user_id)
        raw = await db_session.execute(stmt)
        raw_user = raw.scalar_one_or_none()
        assert raw_user is not None
        assert raw_user.deleted_at is not None


class TestUsuarioRepositoryPIIRoundTrip:
    """TRIANGULATE: cifrado round-trip de los 4 campos PII."""

    async def test_pii_round_trip_all_fields(self, db_session, tenant_factory) -> None:
        """WHEN se crea usuario con PII y se lee, THEN los 4 campos se descifran correctamente."""
        from app.repositories.usuario_repository import UsuarioRepository

        tenant = await tenant_factory()
        repo = UsuarioRepository()

        email = f"rt-{uuid.uuid4().hex[:6]}@test.edu.ar"
        user = await repo.create(
            tenant_id=tenant.id,
            email=email,
            password_plain="pw",
            nombre="Round",
            apellidos="Trip",
            dni="30123456",
            cuil="20301234564",
            cbu="0140123456789012345678",
            alias_cbu="mi.alias.banco",
            session=db_session,
        )

        decrypted = await repo.decrypt_pii(user)
        assert decrypted["dni"] == "30123456"
        assert decrypted["cuil"] == "20301234564"
        assert decrypted["cbu"] == "0140123456789012345678"
        assert decrypted["alias_cbu"] == "mi.alias.banco"
