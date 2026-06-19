"""HiloMensajeRepository — operaciones de acceso a datos para HiloMensaje (C-20).

Filtra SIEMPRE por tenant_id (multi-tenancy row-level).
Softdelete heredado de TenantScopedMixin.
"""

from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hilo_mensaje import HiloMensaje
from app.repositories.base import BaseRepository


class HiloMensajeRepository(BaseRepository[HiloMensaje]):
    """Repositorio para conversaciones internas."""

    def __init__(self) -> None:
        super().__init__(HiloMensaje)

    async def create_hilo(
        self,
        *,
        tenant_id: uuid.UUID,
        iniciado_por: uuid.UUID,
        destinatario_id: uuid.UUID,
        asunto: str,
        session: AsyncSession,
    ) -> HiloMensaje:
        """Crea un hilo de conversación.

        Args:
            tenant_id: Tenant de la sesión.
            iniciado_por: UUID del usuario que inicia (siempre del JWT).
            destinatario_id: UUID del usuario destinatario (validado en el service).
            asunto: Asunto de la conversación.
            session: Sesión async.

        Returns:
            HiloMensaje recién creado.
        """
        hilo = HiloMensaje(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            iniciado_por=iniciado_por,
            destinatario_id=destinatario_id,
            asunto=asunto,
        )
        session.add(hilo)
        await session.flush()
        await session.refresh(hilo)
        return hilo

    async def listar_hilos_de(
        self,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> List[HiloMensaje]:
        """Lista los hilos donde user_id participa (como iniciador o destinatario).

        Filtro por tenant y excluye soft-deleted.
        Ordena por updated_at desc (actividad reciente primero).

        Args:
            tenant_id: Tenant de la sesión.
            user_id: UUID del usuario actual.
            session: Sesión async.
            limit: Tamaño de página.
            offset: Inicio de página.

        Returns:
            Lista de hilos del usuario.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.tenant_id == tenant_id,
                self.model.deleted_at.is_(None),
                or_(
                    self.model.iniciado_por == user_id,
                    self.model.destinatario_id == user_id,
                ),
            )
            .order_by(self.model.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_para_participante(
        self,
        *,
        tenant_id: uuid.UUID,
        hilo_id: uuid.UUID,
        user_id: uuid.UUID,
        session: AsyncSession,
    ) -> Optional[HiloMensaje]:
        """Retorna el hilo solo si user_id es participante del mismo.

        Fail-closed: si no es participante retorna None (→ 403 en el service).

        Args:
            tenant_id: Tenant de la sesión.
            hilo_id: UUID del hilo.
            user_id: UUID del usuario actual.
            session: Sesión async.

        Returns:
            HiloMensaje si existe y el user es participante, None en caso contrario.
        """
        stmt = select(self.model).where(
            self.model.id == hilo_id,
            self.model.tenant_id == tenant_id,
            self.model.deleted_at.is_(None),
            or_(
                self.model.iniciado_por == user_id,
                self.model.destinatario_id == user_id,
            ),
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
