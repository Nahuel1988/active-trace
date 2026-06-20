"""Tests para FacturaService (C-18: factura-gestion).

TDD: RED → GREEN → TRIANGULATE → REFACTOR.
Requiere PostgreSQL (--run-db).
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.factura import FacturaCreate, FacturaUpdate
from app.services.factura_service import FacturaError, FacturaService

pytestmark = pytest.mark.requires_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def tenant(db_session):
    t = Tenant(id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="Test", activo=True)
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


async def _crear_usuario(db_session, tenant_id, facturador=False):
    from app.core.security import encryption_service, email_lookup_hash

    email = f"u-{uuid.uuid4().hex[:8]}@test.com"
    u = User(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        email_encrypted=encryption_service.encrypt(email),
        email_lookup=email_lookup_hash(email),
        password_hash="$argon2id$test",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        is_active=True,
        facturador=facturador,
        cbu_encrypted="cbu_cifrado" if facturador else None,
    )
    db_session.add(u)
    await db_session.flush()
    return u


@pytest.fixture
def svc() -> FacturaService:
    return FacturaService()


def _data(usuario_id: uuid.UUID) -> FacturaCreate:
    return FacturaCreate(
        usuario_id=usuario_id,
        periodo="2026-06",
        detalle="Servicios de docencia",
        referencia_archivo="factura_001.pdf",
        tamano_kb=Decimal("128.5"),
    )


# ---------------------------------------------------------------------------
# Creación
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_crear_factura_exitoso(tenant, svc, db_session):
    """RED: crear factura para usuario facturador retorna FacturaResponse."""
    facturador = await _crear_usuario(db_session, tenant.id, facturador=True)
    await db_session.commit()

    resp = await svc.crear_factura(
        tenant_id=tenant.id, data=_data(facturador.id), session=db_session
    )
    await db_session.commit()

    assert resp.id is not None
    assert resp.estado == "Pendiente"
    assert resp.usuario_id == facturador.id


@pytest.mark.asyncio
async def test_crear_factura_usuario_no_facturador_rechazado(tenant, svc, db_session):
    """TRIANGULATE: usuario sin facturador=True lanza FacturaError 422."""
    no_fact = await _crear_usuario(db_session, tenant.id, facturador=False)
    await db_session.commit()

    with pytest.raises(FacturaError) as exc_info:
        await svc.crear_factura(
            tenant_id=tenant.id, data=_data(no_fact.id), session=db_session
        )
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_crear_factura_usuario_no_encontrado(tenant, svc, db_session):
    """TRIANGULATE: usuario_id inexistente lanza FacturaError 404."""
    with pytest.raises(FacturaError) as exc_info:
        await svc.crear_factura(
            tenant_id=tenant.id,
            data=_data(uuid.uuid4()),
            session=db_session,
        )
    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Edición
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_editar_factura_pendiente(tenant, svc, db_session):
    """RED: editar una Pendiente actualiza el detalle."""
    facturador = await _crear_usuario(db_session, tenant.id, facturador=True)
    await db_session.commit()

    creada = await svc.crear_factura(
        tenant_id=tenant.id, data=_data(facturador.id), session=db_session
    )
    await db_session.commit()

    actualizada = await svc.actualizar_factura(
        tenant_id=tenant.id,
        factura_id=creada.id,
        data=FacturaUpdate(detalle="Nuevo detalle"),
        session=db_session,
    )
    await db_session.commit()
    assert actualizada.detalle == "Nuevo detalle"


@pytest.mark.asyncio
async def test_editar_factura_abonada_rechazado(tenant, svc, db_session):
    """TRIANGULATE: editar una Abonada lanza FacturaError 409."""
    facturador = await _crear_usuario(db_session, tenant.id, facturador=True)
    await db_session.commit()

    creada = await svc.crear_factura(
        tenant_id=tenant.id, data=_data(facturador.id), session=db_session
    )
    await db_session.commit()

    await svc.abonar(tenant_id=tenant.id, factura_id=creada.id, session=db_session)
    await db_session.commit()

    with pytest.raises(FacturaError) as exc_info:
        await svc.actualizar_factura(
            tenant_id=tenant.id,
            factura_id=creada.id,
            data=FacturaUpdate(detalle="No debería actualizarse"),
            session=db_session,
        )
    assert exc_info.value.status_code == 409


# ---------------------------------------------------------------------------
# Abonar
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_abonar_exitoso(tenant, svc, db_session):
    """RED: abonar transiciona estado de Pendiente a Abonada."""
    facturador = await _crear_usuario(db_session, tenant.id, facturador=True)
    await db_session.commit()

    creada = await svc.crear_factura(
        tenant_id=tenant.id, data=_data(facturador.id), session=db_session
    )
    await db_session.commit()

    abonada = await svc.abonar(
        tenant_id=tenant.id, factura_id=creada.id, session=db_session
    )
    await db_session.commit()

    assert abonada.estado == "Abonada"
    assert abonada.abonada_at is not None


@pytest.mark.asyncio
async def test_abonar_dos_veces_rechazado(tenant, svc, db_session):
    """TRIANGULATE: abonar una Abonada lanza FacturaError 409."""
    facturador = await _crear_usuario(db_session, tenant.id, facturador=True)
    await db_session.commit()

    creada = await svc.crear_factura(
        tenant_id=tenant.id, data=_data(facturador.id), session=db_session
    )
    await db_session.commit()

    await svc.abonar(tenant_id=tenant.id, factura_id=creada.id, session=db_session)
    await db_session.commit()

    with pytest.raises(FacturaError) as exc_info:
        await svc.abonar(tenant_id=tenant.id, factura_id=creada.id, session=db_session)
    assert exc_info.value.status_code == 409
