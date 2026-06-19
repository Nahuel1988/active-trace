"""Fixtures compartidos para tests del módulo de auditoría (C-19).

Provee data seeds reutilizables que crean:
  - 2 tenants (A, B)
  - 3 actores por tenant (admin, coordinador, otro docente)
  - Múltiples registros audit_log con variaciones de:
    materia_id (incl. nulo), accion (varios códigos), fecha (3 días distintos)
"""

import uuid
from datetime import datetime, timezone, timedelta

import pytest

from app.models.tenant import Tenant
from app.models.user import User
from app.models.audit_log import AuditLog
from app.repositories.audit_log_repository import AuditLogRepository


TENANT_A_SLUG = "tenant-a-auditoria"
TENANT_B_SLUG = "tenant-b-auditoria"

ACCIONES = [
    "CALIFICACIONES_IMPORTAR",
    "PADRON_CARGAR",
    "COMUNICACION_ENVIAR",
    "ASIGNACION_MODIFICAR",
]


def _make_user(tenant_id: uuid.UUID, email_suffix: str) -> User:
    return User(
        email_encrypted=f"enc-{email_suffix}",
        email_lookup=uuid.uuid4().hex[:64],
        password_hash="$argon2id$hash",
        tenant_id=tenant_id,
    )


def _base_dt() -> datetime:
    """Fecha base: 2026-06-15 12:00 UTC."""
    return datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)


async def seed_audit_data(session, tenant_a, tenant_b, users_a, users_b, materia_ids):
    """Siembra audit_log con datos controlados para pruebas.

    Returns:
        list[AuditLog]: Todos los registros creados (para asserts).
    """
    entries = []
    day_offset = timedelta(days=1)

    # Tenant A: 3 actores × varios días × varias acciones
    for day_i, actor in enumerate(users_a):
        base = _base_dt() + day_i * day_offset
        materia = materia_ids[day_i % len(materia_ids)] if materia_ids else None
        accion = ACCIONES[day_i % len(ACCIONES)]

        entries.append(AuditLog(
            tenant_id=tenant_a.id,
            actor_id=actor.id,
            accion=accion,
            detalle={"origen": "seed"},
            filas_afectadas=(day_i + 1) * 10,
            ip=f"10.0.{day_i}.1",
            user_agent="pytest-auditoria",
            materia_id=materia,
        ))
        # Forzar fecha: seteamos fecha_hora después de flush
        # (server_default = now(), lo sobrescribimos)

    # Tenant B: 1 actor, 1 registro (para test de aislamiento)
    entries.append(AuditLog(
        tenant_id=tenant_b.id,
        actor_id=users_b[0].id,
        accion="PADRON_CARGAR",
        detalle={"origen": "seed-b"},
        filas_afectadas=5,
        ip="10.99.0.1",
        user_agent="pytest-b",
    ))

    for e in entries:
        session.add(e)
    await session.flush()

    # Forzar fechas personalizadas (post-insert)
    for i, e in enumerate(entries):
        e.fecha_hora = _base_dt() + (i % 3) * timedelta(days=1)
    await session.flush()

    return entries


@pytest.fixture(scope="module")
def auditoria_tenant_a() -> Tenant:
    return Tenant(id=uuid.uuid4(), slug=TENANT_A_SLUG, nombre="Tenant A Auditoría")


@pytest.fixture(scope="module")
def auditoria_tenant_b() -> Tenant:
    return Tenant(id=uuid.uuid4(), slug=TENANT_B_SLUG, nombre="Tenant B Auditoría")
