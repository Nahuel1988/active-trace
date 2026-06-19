"""Tests para AsignacionService — TDD C-07.

RED: tests fallan porque el servicio no existe.
GREEN: se crea el servicio y los tests pasan.
TRIANGULATE: validaciones de rol×contexto, ciclo de responsables, ADMIN rechazado.
"""

import uuid
import pytest
from datetime import datetime, timezone, timedelta

pytestmark = pytest.mark.requires_db


async def _make_tenant_with_user_and_role(db_session, tenant_factory, role_code="PROFESOR"):
    """Helper: crea tenant, usuario y rol para tests de asignacion."""
    from app.repositories.usuario_repository import UsuarioRepository
    from app.models.role import Role

    tenant = await tenant_factory(slug=f"asig-{uuid.uuid4().hex[:6]}")

    user_repo = UsuarioRepository()
    user = await user_repo.create(
        tenant_id=tenant.id,
        email=f"u-{uuid.uuid4().hex[:6]}@test.edu.ar",
        password_plain="pw",
        nombre="Test",
        apellidos="User",
        session=db_session,
    )

    role = Role(
        tenant_id=tenant.id,
        code=role_code,
        nombre=role_code,
    )
    db_session.add(role)
    await db_session.flush()
    await db_session.refresh(role)

    return tenant, user, role


class TestAsignacionServiceValidacionRolContexto:
    """Scenario: combinaciones válidas rol × contexto."""

    async def test_profesor_sin_materia_rechazado(self, db_session, tenant_factory) -> None:
        """WHEN PROFESOR sin materia_id, THEN ServiceError 422."""
        from app.services.asignacion_service import AsignacionService, AsignacionServiceError

        tenant, user, role = await _make_tenant_with_user_and_role(
            db_session, tenant_factory, "PROFESOR"
        )
        service = AsignacionService()

        with pytest.raises(AsignacionServiceError) as excinfo:
            await service.create(
                tenant_id=tenant.id,
                actor_id=uuid.uuid4(),
                usuario_id=user.id,
                role_id=role.id,
                role_code="PROFESOR",
                desde=datetime.now(timezone.utc),
                # sin materia_id — debe fallar
                carrera_id=uuid.uuid4(),
                cohorte_id=uuid.uuid4(),
                session=db_session,
            )
        assert excinfo.value.status_code == 422
        assert "materia_id" in excinfo.value.detail.lower()

    async def test_coordinador_solo_carrera_valido(self, db_session, tenant_factory) -> None:
        """WHEN COORDINADOR con solo carrera_id, THEN persiste correctamente."""
        from app.services.asignacion_service import AsignacionService
        from app.models.carrera import Carrera

        tenant, user, role = await _make_tenant_with_user_and_role(
            db_session, tenant_factory, "COORDINADOR"
        )

        # Crear carrera para FK válida
        carrera = Carrera(
            tenant_id=tenant.id,
            codigo=f"CAR-{uuid.uuid4().hex[:4]}",
            nombre="Carrera Test",
        )
        db_session.add(carrera)
        await db_session.flush()

        service = AsignacionService()
        asig = await service.create(
            tenant_id=tenant.id,
            actor_id=uuid.uuid4(),
            usuario_id=user.id,
            role_id=role.id,
            role_code="COORDINADOR",
            desde=datetime.now(timezone.utc),
            carrera_id=carrera.id,
            session=db_session,
        )
        assert asig.id is not None
        assert asig.materia_id is None
        assert asig.cohorte_id is None

    async def test_admin_rechazado_en_asignacion(self, db_session, tenant_factory) -> None:
        """WHEN se crea Asignacion con rol ADMIN, THEN ServiceError 422."""
        from app.services.asignacion_service import AsignacionService, AsignacionServiceError

        tenant, user, role = await _make_tenant_with_user_and_role(
            db_session, tenant_factory, "ADMIN"
        )
        service = AsignacionService()

        with pytest.raises(AsignacionServiceError) as excinfo:
            await service.create(
                tenant_id=tenant.id,
                actor_id=uuid.uuid4(),
                usuario_id=user.id,
                role_id=role.id,
                role_code="ADMIN",
                desde=datetime.now(timezone.utc),
                session=db_session,
            )
        assert excinfo.value.status_code == 422
        assert "admin" in excinfo.value.detail.lower() or "user_role" in excinfo.value.detail.lower()

    async def test_finanzas_rechazado_en_asignacion(self, db_session, tenant_factory) -> None:
        """WHEN se crea Asignacion con rol FINANZAS, THEN ServiceError 422."""
        from app.services.asignacion_service import AsignacionService, AsignacionServiceError

        tenant, user, role = await _make_tenant_with_user_and_role(
            db_session, tenant_factory, "FINANZAS"
        )
        service = AsignacionService()

        with pytest.raises(AsignacionServiceError) as excinfo:
            await service.create(
                tenant_id=tenant.id,
                actor_id=uuid.uuid4(),
                usuario_id=user.id,
                role_id=role.id,
                role_code="FINANZAS",
                desde=datetime.now(timezone.utc),
                session=db_session,
            )
        assert excinfo.value.status_code == 422


class TestAsignacionServiceAutoSupervision:
    """Scenario: auto-supervisión rechazada."""

    async def test_autosupervision_rechazada(self, db_session, tenant_factory) -> None:
        """WHEN responsable_id == usuario_id, THEN ServiceError 422."""
        from app.services.asignacion_service import AsignacionService, AsignacionServiceError

        tenant, user, role = await _make_tenant_with_user_and_role(
            db_session, tenant_factory, "NEXO"
        )
        service = AsignacionService()

        with pytest.raises(AsignacionServiceError) as excinfo:
            await service.create(
                tenant_id=tenant.id,
                actor_id=uuid.uuid4(),
                usuario_id=user.id,
                role_id=role.id,
                role_code="NEXO",
                desde=datetime.now(timezone.utc),
                responsable_id=user.id,  # mismo usuario
                session=db_session,
            )
        assert excinfo.value.status_code == 422
        assert "responsable" in excinfo.value.detail.lower() or "auto" in excinfo.value.detail.lower()


class TestAsignacionServiceVigencia:
    """Scenario: desde <= hasta."""

    async def test_hasta_antes_de_desde_rechazado(self, db_session, tenant_factory) -> None:
        """WHEN hasta < desde, THEN ServiceError 422."""
        from app.services.asignacion_service import AsignacionService, AsignacionServiceError

        tenant, user, role = await _make_tenant_with_user_and_role(
            db_session, tenant_factory, "NEXO"
        )
        service = AsignacionService()

        with pytest.raises(AsignacionServiceError) as excinfo:
            await service.create(
                tenant_id=tenant.id,
                actor_id=uuid.uuid4(),
                usuario_id=user.id,
                role_id=role.id,
                role_code="NEXO",
                desde=datetime(2026, 9, 1, tzinfo=timezone.utc),
                hasta=datetime(2026, 8, 31, tzinfo=timezone.utc),
                session=db_session,
            )
        assert excinfo.value.status_code == 422
        assert "hasta" in excinfo.value.detail.lower()


class TestAsignacionServiceCicloResponsables:
    """TRIANGULATE: detección de ciclos en cadena de responsables."""

    async def test_ciclo_de_dos_detectado(self, db_session, tenant_factory) -> None:
        """WHEN A reporta a B y B intenta reportar a A, THEN ServiceError 422 (ciclo)."""
        from app.services.asignacion_service import AsignacionService, AsignacionServiceError
        from app.repositories.usuario_repository import UsuarioRepository

        tenant = await tenant_factory(slug=f"ciclo-{uuid.uuid4().hex[:6]}")
        user_repo = UsuarioRepository()

        # Crear usuarios A y B
        user_a = await user_repo.create(
            tenant_id=tenant.id,
            email=f"a-{uuid.uuid4().hex[:6]}@test.edu.ar",
            password_plain="pw",
            nombre="A",
            apellidos="A",
            session=db_session,
        )
        user_b = await user_repo.create(
            tenant_id=tenant.id,
            email=f"b-{uuid.uuid4().hex[:6]}@test.edu.ar",
            password_plain="pw",
            nombre="B",
            apellidos="B",
            session=db_session,
        )

        from app.models.role import Role
        role = Role(tenant_id=tenant.id, code="NEXO", nombre="NEXO")
        db_session.add(role)
        await db_session.flush()

        service = AsignacionService()

        # A reporta a B (válido)
        await service.create(
            tenant_id=tenant.id,
            actor_id=uuid.uuid4(),
            usuario_id=user_a.id,
            role_id=role.id,
            role_code="NEXO",
            desde=datetime.now(timezone.utc),
            responsable_id=user_b.id,
            session=db_session,
        )

        # B intenta reportar a A → ciclo
        with pytest.raises(AsignacionServiceError) as excinfo:
            await service.create(
                tenant_id=tenant.id,
                actor_id=uuid.uuid4(),
                usuario_id=user_b.id,
                role_id=role.id,
                role_code="NEXO",
                desde=datetime.now(timezone.utc),
                responsable_id=user_a.id,
                session=db_session,
            )
        assert excinfo.value.status_code == 422
        assert "ciclo" in excinfo.value.detail.lower()
