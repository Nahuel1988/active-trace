"""Tests para UsuarioService — TDD C-07.

RED: tests fallan porque el servicio no existe.
GREEN: se crea el servicio y los tests pasan.
TRIANGULATE: audit log no contiene PII, email único por tenant.
"""

import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

pytestmark = pytest.mark.requires_db


class TestUsuarioServiceCreate:
    """Scenario: creación de usuario happy path."""

    async def test_create_usuario_happy_path(self, db_session, tenant_factory) -> None:
        """WHEN se crea un usuario, THEN retorna el usuario con UUID."""
        from app.services.usuario_service import UsuarioService

        tenant = await tenant_factory()
        service = UsuarioService()

        actor_id = uuid.uuid4()
        user = await service.create(
            tenant_id=tenant.id,
            actor_id=actor_id,
            email=f"svc-{uuid.uuid4().hex[:6]}@test.edu.ar",
            password_plain="Segura1234!",
            nombre="Juan",
            apellidos="García",
            session=db_session,
        )

        assert user.id is not None
        assert user.tenant_id == tenant.id
        assert user.nombre == "Juan"

    async def test_create_usuario_with_pii(self, db_session, tenant_factory) -> None:
        """WHEN ADMIN crea usuario con PII, THEN campos encrypted contienen ciphertext."""
        from app.services.usuario_service import UsuarioService

        tenant = await tenant_factory()
        service = UsuarioService()

        user = await service.create(
            tenant_id=tenant.id,
            actor_id=uuid.uuid4(),
            email=f"pii-svc-{uuid.uuid4().hex[:6]}@test.edu.ar",
            password_plain="pw",
            nombre="María",
            apellidos="López",
            dni="30123456",
            session=db_session,
        )

        assert user.dni_encrypted is not None
        assert "30123456" not in user.dni_encrypted

    async def test_create_duplicate_email_raises(self, db_session, tenant_factory) -> None:
        """WHEN se crea usuario con email duplicado en mismo tenant, THEN ServiceError 400."""
        from app.services.usuario_service import UsuarioService, UsuarioServiceError

        tenant = await tenant_factory()
        service = UsuarioService()
        email = f"dup-{uuid.uuid4().hex[:6]}@test.edu.ar"

        await service.create(
            tenant_id=tenant.id,
            actor_id=uuid.uuid4(),
            email=email,
            password_plain="pw",
            nombre="Test",
            apellidos="A",
            session=db_session,
        )

        with pytest.raises(UsuarioServiceError) as excinfo:
            await service.create(
                tenant_id=tenant.id,
                actor_id=uuid.uuid4(),
                email=email,
                password_plain="pw",
                nombre="Test",
                apellidos="B",
                session=db_session,
            )
        assert excinfo.value.status_code == 400


class TestUsuarioServiceSoftDelete:
    """Scenario: soft delete preserva el registro."""

    async def test_soft_delete_returns_true(self, db_session, tenant_factory) -> None:
        """WHEN se soft-deletea un usuario, THEN el servicio retorna True."""
        from app.services.usuario_service import UsuarioService

        tenant = await tenant_factory()
        service = UsuarioService()

        user = await service.create(
            tenant_id=tenant.id,
            actor_id=uuid.uuid4(),
            email=f"del-svc-{uuid.uuid4().hex[:6]}@test.edu.ar",
            password_plain="pw",
            nombre="Delete",
            apellidos="Me",
            session=db_session,
        )

        result = await service.delete(
            tenant_id=tenant.id,
            id=user.id,
            actor_id=uuid.uuid4(),
            session=db_session,
        )
        assert result is True


class TestUsuarioServiceAuditLogNoPII:
    """TRIANGULATE: audit log no contiene PII en claro."""

    async def test_audit_log_detail_no_pii(self, db_session, tenant_factory) -> None:
        """WHEN se crea usuario con PII, THEN el detalle del audit log NO contiene PII en claro."""
        from app.services.usuario_service import UsuarioService
        from app.repositories.audit_log_repository import AuditLogRepository

        tenant = await tenant_factory()
        service = UsuarioService()
        actor_id = uuid.uuid4()
        dni = "30123456"

        await service.create(
            tenant_id=tenant.id,
            actor_id=actor_id,
            email=f"audit-{uuid.uuid4().hex[:6]}@test.edu.ar",
            password_plain="pw",
            nombre="Audit",
            apellidos="Test",
            dni=dni,
            session=db_session,
        )

        audit_repo = AuditLogRepository()
        entries = await audit_repo.list(tenant_id=tenant.id, session=db_session)
        crear_entries = [e for e in entries if e.accion == "USUARIO_CREAR"]

        assert len(crear_entries) > 0
        for entry in crear_entries:
            # El campo detalle (JSONB) no debe contener PII en claro
            detalle_str = str(entry.detalle)
            assert dni not in detalle_str, (
                f"DNI en claro encontrado en audit log detalle: {detalle_str}"
            )
