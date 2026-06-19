import uuid
from datetime import datetime, timezone, timedelta

import pytest
from httpx import AsyncClient, ASGITransport

pytestmark = pytest.mark.requires_db


class TestAvisoEndpoints:
    @pytest.fixture(autouse=True)
    async def _setup(self, db_session, create_test_schema):
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.role import Role
        from app.models.permiso import Permiso, RolPermiso
        from app.core.security import hash_password

        self.tenant = Tenant(id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T")
        db_session.add(self.tenant)
        await db_session.flush()

        self.user = User(
            id=uuid.uuid4(),
            tenant_id=self.tenant.id,
            email_encrypted="enc",
            email_lookup=f"lookup-{uuid.uuid4().hex[:8]}",
            password_hash=hash_password("secret"),
            is_active=True,
        )
        db_session.add(self.user)
        await db_session.flush()

        role = Role(
            id=uuid.uuid4(),
            tenant_id=self.tenant.id,
            code="admin",
            nombre="Admin",
        )
        db_session.add(role)
        await db_session.flush()

        from app.models.role import UserRole
        ur = UserRole(
            tenant_id=self.tenant.id,
            user_id=self.user.id,
            role_id=role.id,
            desde=datetime.now(timezone.utc) - timedelta(days=30),
            hasta=datetime.now(timezone.utc) + timedelta(days=30),
        )
        db_session.add(ur)
        await db_session.flush()

        permiso = Permiso(
            id=uuid.uuid4(),
            tenant_id=self.tenant.id,
            modulo="avisos",
            accion="publicar",
            code="avisos:publicar",
        )
        db_session.add(permiso)
        await db_session.flush()

        rp = RolPermiso(
            tenant_id=self.tenant.id,
            role_id=role.id,
            permiso_id=permiso.id,
            scope="global",
        )
        db_session.add(rp)
        await db_session.flush()

    async def _login(self, db_session):
        from app.core.dependencies import get_settings
        from app.services.token_service import TokenService
        from app.repositories.refresh_token_repository import RefreshTokenRepository

        settings = get_settings()
        token_svc = TokenService(refresh_token_repo=RefreshTokenRepository())
        tokens = await token_svc.issue_token_pair(
            user=self.user,
            session=db_session,
        )
        return tokens["access_token"]

    async def _get_client(self, db_session):
        from app.main import create_app
        from app.core.dependencies import get_db

        app = create_app()

        async def _override_db():
            yield db_session

        app.dependency_overrides[get_db] = _override_db
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    async def test_create_aviso_200(self, db_session):
        client = await self._get_client(db_session)
        token = await self._login(db_session)

        now = datetime.now(timezone.utc)
        resp = await client.post(
            "/api/v1/avisos/",
            json={
                "titulo": "Aviso de prueba",
                "cuerpo": "Contenido del aviso",
                "alcance": "global",
                "severidad": "info",
                "inicio_en": now.isoformat(),
                "fin_en": (now + timedelta(days=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["titulo"] == "Aviso de prueba"

    async def test_create_aviso_403(self, db_session):
        from app.models.role import Role, UserRole
        from app.models.user import User
        from datetime import datetime, timezone, timedelta

        client = await self._get_client(db_session)

        other_user = User(
            id=uuid.uuid4(),
            tenant_id=self.tenant.id,
            email_encrypted="enc2",
            email_lookup=f"lookup-{uuid.uuid4().hex[:8]}",
            password_hash="hash",
            is_active=True,
        )
        db_session.add(other_user)
        await db_session.flush()

        role = Role(id=uuid.uuid4(), tenant_id=self.tenant.id, code="alumno", nombre="Alumno")
        db_session.add(role)
        await db_session.flush()

        ur = UserRole(
            tenant_id=self.tenant.id,
            user_id=other_user.id,
            role_id=role.id,
            desde=datetime.now(timezone.utc) - timedelta(days=30),
            hasta=datetime.now(timezone.utc) + timedelta(days=30),
        )
        db_session.add(ur)
        await db_session.flush()

        from app.services.token_service import TokenService
        from app.repositories.refresh_token_repository import RefreshTokenRepository
        token_svc = TokenService(refresh_token_repo=RefreshTokenRepository())
        tokens = await token_svc.issue_token_pair(
            user=other_user,
            session=db_session,
        )
        token = tokens["access_token"]

        now = datetime.now(timezone.utc)
        resp = await client.post(
            "/api/v1/avisos/",
            json={
                "titulo": "Sin permiso",
                "cuerpo": "No deberia crear",
                "alcance": "global",
                "severidad": "info",
                "inicio_en": now.isoformat(),
                "fin_en": (now + timedelta(days=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    async def test_list_visibles_returns_global(self, db_session):
        from app.models.aviso import Aviso, AlcanceAviso, SeveridadAviso

        client = await self._get_client(db_session)
        token = await self._login(db_session)

        now = datetime.now(timezone.utc)
        aviso = Aviso(
            tenant_id=self.tenant.id,
            titulo="Visible",
            cuerpo="Cuerpo",
            alcance=AlcanceAviso.Global,
            severidad=SeveridadAviso.Info,
            inicio_en=now - timedelta(days=1),
            fin_en=now + timedelta(days=1),
            activo=True,
        )
        db_session.add(aviso)
        await db_session.flush()

        resp = await client.get(
            "/api/v1/avisos/visibles",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["titulo"] == "Visible"

    async def test_ack_aviso(self, db_session):
        from app.models.aviso import Aviso, AlcanceAviso, SeveridadAviso

        client = await self._get_client(db_session)
        token = await self._login(db_session)

        now = datetime.now(timezone.utc)
        aviso = Aviso(
            tenant_id=self.tenant.id,
            titulo="Para ack",
            cuerpo="Cuerpo",
            alcance=AlcanceAviso.Global,
            severidad=SeveridadAviso.Info,
            inicio_en=now - timedelta(days=1),
            fin_en=now + timedelta(days=1),
            activo=True,
        )
        db_session.add(aviso)
        await db_session.flush()

        resp = await client.post(
            f"/api/v1/avisos/{aviso.id}/ack",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["aviso_id"] == str(aviso.id)
