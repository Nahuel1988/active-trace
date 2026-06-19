"""MensajeInternoRepository — operaciones de acceso a datos para MensajeInterno (C-20).

Filtra SIEMPRE por tenant_id (multi-tenancy row-level).
Softdelete heredado de TenantScopedMixin (deleted_at).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mensaje_interno import MensajeInterno
from app.repositories.base import BaseRepository


class MensajeInternoRepository(BaseRepository[MensajeInterno]):
    """Repositorio para los mensajes de un hilo interno."""

    def __init__(self) -> None:
        super().__init__(MensajeInterno)

    async def agregar_mensaje(
        self,
        *,
        tenant_id: uuid.UUID,
        hilo_id: uuid.UUID,
        autor_id: uuid.UUID,
        cuerpo: str,
        session: AsyncSession,
    ) -> MensajeInterno:
        """Agrega un mensaje a un hilo existente.

        El autor_id SIEMPRE viene del JWT (nunca del body).

        Args:
            tenant_id: Tenant de la sesión.
            hilo_id: UUID del hilo.
            autor_id: UUID del autor (del JWT, nunca del body).
            cuerpo: Texto del mensaje.
            session: Sesión async.

        Returns:
            MensajeInterno recién creado.
        """
        msg = MensajeInterno(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            hilo_id=hilo_id,
            autor_id=autor_id,
            cuerpo=cuerpo,
        )
        session.add(msg)
        await session.flush()
        await session.refresh(msg)
        return msg

    async def listar_mensajes(
        self,
        *,
        tenant_id: uuid.UUID,
        hilo_id: uuid.UUID,
        session: AsyncSession,
    ) -> List[MensajeInterno]:
        """Lista los mensajes de un hilo ordenados cronológicamente.

        Solo filtra mensajes no soft-deleted del tenant y hilo correctos.

        Args:
            tenant_id: Tenant de la sesión.
            hilo_id: UUID del hilo.
            session: Sesión async.

        Returns:
            Lista de MensajeInterno ordenados por creado_at asc.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.tenant_id == tenant_id,
                self.model.hilo_id == hilo_id,
                self.model.deleted_at.is_(None),
            )
            .order_by(self.model.creado_at.asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def marcar_leidos(
        self,
        *,
        tenant_id: uuid.UUID,
        hilo_id: uuid.UUID,
        destinatario_id: uuid.UUID,
        session: AsyncSession,
    ) -> None:
        """Marca como leídos los mensajes del hilo NO escritos por el destinatario.

        Solo actualiza mensajes donde leido_at IS NULL y autor_id != destinatario_id.
        (Los mensajes propios no necesitan marcarse como leídos.)

        Args:
            tenant_id: Tenant de la sesión.
            hilo_id: UUID del hilo.
            destinatario_id: UUID del usuario que lee (del JWT).
            session: Sesión async.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            update(self.model)
            .where(
                self.model.tenant_id == tenant_id,
                self.model.hilo_id == hilo_id,
                self.model.deleted_at.is_(None),
                self.model.leido_at.is_(None),
                self.model.autor_id != destinatario_id,
            )
            .values(leido_at=now)
        )
        await session.execute(stmt)
        await session.flush()
