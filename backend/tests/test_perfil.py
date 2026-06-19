"""Tests TDD para C-20: perfil-y-mensajeria-interna — módulo de perfil propio.

Cubre:
    - Modelo User: campo modalidad_cobro
    - Schemas: PerfilRead, PerfilUpdate (CUIL read-only, extra='forbid')
    - UsuarioRepository: get_perfil, update_perfil (tenant isolation)
    - PerfilService: descifra PII, rechaza CUIL en update
    - Router: GET /api/perfil, PATCH /api/perfil (identidad desde JWT)

Requiere DB real para tests de repositorio/servicio/router (--run-db).
Los tests de schema/modelo son puros (sin DB).
"""

from __future__ import annotations

import uuid

import pytest

# ============================================================
# 2. Modelo — modalidad_cobro
# ============================================================


class TestUserModelModalidadCobro:
    """2.1 RED: User tiene modalidad_cobro con valores factura/liquidacion."""

    def test_user_has_modalidad_cobro_attribute(self) -> None:
        """WHEN se inspeccionan columnas de User, THEN modalidad_cobro está presente."""
        from sqlalchemy import inspect as sa_inspect
        from app.models.user import User

        mapper = sa_inspect(User)
        col_names = {c.key for c in mapper.column_attrs}
        assert "modalidad_cobro" in col_names

    def test_modalidad_cobro_column_exists_in_table_args(self) -> None:
        """WHEN User se mapea, THEN modalidad_cobro es una columna SQLAlchemy."""
        from sqlalchemy import inspect as sa_inspect
        from app.models.user import User

        mapper = sa_inspect(User)
        col_names = [c.key for c in mapper.column_attrs]
        assert "modalidad_cobro" in col_names

    def test_modalidad_cobro_is_nullable(self) -> None:
        """WHEN se lee la columna, THEN es nullable (convivencia con users pre-existentes)."""
        from sqlalchemy import inspect as sa_inspect
        from app.models.user import User

        mapper = sa_inspect(User)
        col = next(c for c in mapper.columns if c.key == "modalidad_cobro")
        assert col.nullable is True


# ============================================================
# 4. Schemas Pydantic
# ============================================================


class TestPerfilUpdateSchema:
    """4.1 RED: PerfilUpdate rechaza cuil y campos extras."""

    def test_perfil_update_rejects_cuil(self) -> None:
        """WHEN se envía cuil en PerfilUpdate, THEN ValidationError (extra='forbid')."""
        from pydantic import ValidationError
        from app.schemas.perfil import PerfilUpdate

        with pytest.raises(ValidationError) as exc_info:
            PerfilUpdate(cuil="20301234564")
        errors = exc_info.value.errors()
        assert any(e["type"] == "extra_forbidden" for e in errors)

    def test_perfil_update_rejects_unknown_fields(self) -> None:
        """WHEN se envía campo desconocido, THEN ValidationError."""
        from pydantic import ValidationError
        from app.schemas.perfil import PerfilUpdate

        with pytest.raises(ValidationError) as exc_info:
            PerfilUpdate(is_admin=True)
        errors = exc_info.value.errors()
        assert any(e["type"] == "extra_forbidden" for e in errors)

    def test_perfil_update_accepts_valid_fields(self) -> None:
        """WHEN se envían campos válidos, THEN PerfilUpdate se construye sin error."""
        from app.schemas.perfil import PerfilUpdate

        dto = PerfilUpdate(nombre="Juan", regional="Córdoba")
        assert dto.nombre == "Juan"
        assert dto.regional == "Córdoba"

    def test_perfil_update_modalidad_cobro_rejects_invalid(self) -> None:
        """WHEN modalidad_cobro tiene valor inválido, THEN ValidationError."""
        from pydantic import ValidationError
        from app.schemas.perfil import PerfilUpdate

        with pytest.raises(ValidationError):
            PerfilUpdate(modalidad_cobro="efectivo")

    def test_perfil_update_modalidad_cobro_accepts_factura(self) -> None:
        """WHEN modalidad_cobro='factura', THEN válido."""
        from app.schemas.perfil import PerfilUpdate

        dto = PerfilUpdate(modalidad_cobro="factura")
        assert dto.modalidad_cobro == "factura"

    def test_perfil_update_modalidad_cobro_accepts_liquidacion(self) -> None:
        """WHEN modalidad_cobro='liquidacion', THEN válido."""
        from app.schemas.perfil import PerfilUpdate

        dto = PerfilUpdate(modalidad_cobro="liquidacion")
        assert dto.modalidad_cobro == "liquidacion"


class TestPerfilReadSchema:
    """4.1 RED: PerfilRead expone PII descifrada."""

    def test_perfil_read_has_pii_fields(self) -> None:
        """WHEN se construye PerfilRead, THEN tiene dni, cuil, cbu, alias_cbu."""
        from app.schemas.perfil import PerfilRead

        dto = PerfilRead(
            id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            email="test@example.com",
            nombre="Juan",
            apellidos="García",
            legajo=None,
            legajo_profesional=None,
            banco=None,
            regional=None,
            facturador=False,
            is_active=True,
            dni="30123456",
            cuil="20301234564",
            cbu="012345678901234567890",
            alias_cbu="mi.alias",
            modalidad_cobro=None,
        )
        assert dto.cuil == "20301234564"
        assert dto.dni == "30123456"

    def test_perfil_read_rejects_extra_fields(self) -> None:
        """WHEN se envía campo extra en PerfilRead, THEN ValidationError."""
        from pydantic import ValidationError
        from app.schemas.perfil import PerfilRead

        with pytest.raises(ValidationError):
            PerfilRead(
                id=str(uuid.uuid4()),
                tenant_id=str(uuid.uuid4()),
                campo_inventado="hola",
            )


# ============================================================
# 3. Repositorio de perfil
# ============================================================


pytestmark_db = pytest.mark.requires_db


@pytest.mark.requires_db
class TestUsuarioRepositoryGetPerfil:
    """3.1 RED: get_perfil filtra por tenant, update_perfil actualiza."""

    async def test_get_perfil_returns_user(self, db_session, tenant_factory) -> None:
        """WHEN se llama get_perfil con id y tenant válidos, THEN retorna el usuario."""
        from app.repositories.usuario_repository import UsuarioRepository

        tenant = await tenant_factory()
        repo = UsuarioRepository()
        user = await repo.create(
            tenant_id=tenant.id,
            email=f"perfil-{uuid.uuid4().hex[:6]}@test.edu.ar",
            password_plain="Pw12345!",
            nombre="Ana",
            apellidos="Pérez",
            session=db_session,
        )

        found = await repo.get_perfil(
            tenant_id=tenant.id, user_id=user.id, session=db_session
        )
        assert found is not None
        assert found.id == user.id

    async def test_get_perfil_cross_tenant_returns_none(
        self, db_session, tenant_factory
    ) -> None:
        """WHEN se busca con tenant_id incorrecto, THEN None (aislamiento)."""
        from app.repositories.usuario_repository import UsuarioRepository

        tenant_a = await tenant_factory(slug=f"gp-a-{uuid.uuid4().hex[:4]}")
        tenant_b = await tenant_factory(slug=f"gp-b-{uuid.uuid4().hex[:4]}")
        repo = UsuarioRepository()
        user = await repo.create(
            tenant_id=tenant_a.id,
            email=f"iso-{uuid.uuid4().hex[:6]}@test.edu.ar",
            password_plain="Pw12345!",
            nombre="Tenant",
            apellidos="A",
            session=db_session,
        )

        not_found = await repo.get_perfil(
            tenant_id=tenant_b.id, user_id=user.id, session=db_session
        )
        assert not_found is None

    async def test_update_perfil_updates_non_pii_field(
        self, db_session, tenant_factory
    ) -> None:
        """WHEN update_perfil con regional, THEN se actualiza y el resto se conserva."""
        from app.repositories.usuario_repository import UsuarioRepository

        tenant = await tenant_factory()
        repo = UsuarioRepository()
        user = await repo.create(
            tenant_id=tenant.id,
            email=f"upd-{uuid.uuid4().hex[:6]}@test.edu.ar",
            password_plain="Pw12345!",
            nombre="Mario",
            apellidos="Ruiz",
            banco="Galicia",
            session=db_session,
        )

        updated = await repo.update_perfil(
            tenant_id=tenant.id,
            user_id=user.id,
            data={"regional": "Mendoza"},
            session=db_session,
        )
        assert updated is not None
        assert updated.regional == "Mendoza"
        assert updated.banco == "Galicia"  # resto conservado

    async def test_update_perfil_partial_preserves_rest(
        self, db_session, tenant_factory
    ) -> None:
        """TRIANGULATE: actualización parcial (solo un campo) preserva los demás."""
        from app.repositories.usuario_repository import UsuarioRepository

        tenant = await tenant_factory()
        repo = UsuarioRepository()
        user = await repo.create(
            tenant_id=tenant.id,
            email=f"part-{uuid.uuid4().hex[:6]}@test.edu.ar",
            password_plain="Pw12345!",
            nombre="Elena",
            apellidos="Sosa",
            regional="Buenos Aires",
            banco="Nación",
            session=db_session,
        )

        updated = await repo.update_perfil(
            tenant_id=tenant.id,
            user_id=user.id,
            data={"banco": "Santander"},
            session=db_session,
        )
        assert updated.banco == "Santander"
        assert updated.nombre == "Elena"
        assert updated.regional == "Buenos Aires"


# ============================================================
# 5. Servicio de perfil
# ============================================================


@pytest.mark.requires_db
class TestPerfilService:
    """5.1 RED: perfil_service.get_perfil descifra PII; update_perfil cifra PII."""

    async def test_get_perfil_decrypts_pii(self, db_session, tenant_factory) -> None:
        """WHEN get_perfil, THEN dni/cuil/cbu/alias_cbu aparecen descifrados."""
        from app.repositories.usuario_repository import UsuarioRepository
        from app.services.perfil_service import PerfilService

        tenant = await tenant_factory()
        usuario_repo = UsuarioRepository()
        service = PerfilService(usuario_repo=usuario_repo)

        user = await usuario_repo.create(
            tenant_id=tenant.id,
            email=f"svc-get-{uuid.uuid4().hex[:6]}@test.edu.ar",
            password_plain="Pw12345!",
            nombre="Clara",
            apellidos="Torres",
            dni="31111111",
            cuil="27311111118",
            cbu="0140999900000012345678",
            alias_cbu="clara.torres.nacion",
            session=db_session,
        )

        result = await service.get_perfil(
            tenant_id=tenant.id, user_id=user.id, session=db_session
        )
        assert result["dni"] == "31111111"
        assert result["cuil"] == "27311111118"
        assert result["cbu"] == "0140999900000012345678"
        assert result["alias_cbu"] == "clara.torres.nacion"

    async def test_update_perfil_encrypts_cbu(self, db_session, tenant_factory) -> None:
        """WHEN update_perfil con cbu en claro, THEN cbu_encrypted != cbu en claro."""
        from app.repositories.usuario_repository import UsuarioRepository
        from app.services.perfil_service import PerfilService

        tenant = await tenant_factory()
        usuario_repo = UsuarioRepository()
        service = PerfilService(usuario_repo=usuario_repo)

        user = await usuario_repo.create(
            tenant_id=tenant.id,
            email=f"svc-enc-{uuid.uuid4().hex[:6]}@test.edu.ar",
            password_plain="Pw12345!",
            nombre="Pablo",
            apellidos="Díaz",
            session=db_session,
        )

        updated_user = await service.update_perfil(
            tenant_id=tenant.id,
            user_id=user.id,
            data={"cbu": "0110590520000012345678"},
            session=db_session,
        )
        assert updated_user.cbu_encrypted is not None
        assert "0110590520000012345678" not in updated_user.cbu_encrypted

    async def test_update_perfil_cuil_unchanged(
        self, db_session, tenant_factory
    ) -> None:
        """TRIANGULATE: CUIL inalterado tras update_perfil."""
        from app.repositories.usuario_repository import UsuarioRepository
        from app.services.perfil_service import PerfilService
        from app.core.security import encryption_service

        tenant = await tenant_factory()
        usuario_repo = UsuarioRepository()
        service = PerfilService(usuario_repo=usuario_repo)

        cuil_original = "20301234564"
        user = await usuario_repo.create(
            tenant_id=tenant.id,
            email=f"svc-cuil-{uuid.uuid4().hex[:6]}@test.edu.ar",
            password_plain="Pw12345!",
            nombre="Rosa",
            apellidos="Flores",
            cuil=cuil_original,
            session=db_session,
        )

        # update_perfil NO debe tocar cuil
        await service.update_perfil(
            tenant_id=tenant.id,
            user_id=user.id,
            data={"banco": "BBVA"},
            session=db_session,
        )

        # Re-read user
        refreshed = await usuario_repo.get_perfil(
            tenant_id=tenant.id, user_id=user.id, session=db_session
        )
        cuil_decrypted = (
            encryption_service.decrypt(refreshed.cuil_encrypted)
            if refreshed.cuil_encrypted
            else None
        )
        assert cuil_decrypted == cuil_original


# ============================================================
# 13. Verificación: NO logout propio
# ============================================================


class TestNoLogoutInPerfil:
    """13.2: No existe endpoint de logout bajo /api/perfil."""

    def test_perfil_router_has_no_logout_endpoint(self) -> None:
        """WHEN se inspeccionan las rutas del router de perfil, THEN no hay /logout."""
        from app.api.v1.routers.perfil import router

        route_paths = [r.path for r in router.routes]
        assert not any("logout" in path for path in route_paths)
