"""BaseRepository genérico con tenant-scoping obligatorio."""

from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Repositorio base con filtro obligatorio por tenant y soft-delete.

    Todos los métodos de lectura filtran por ``tenant_id`` y excluyen
    registros soft-deleteados (``deleted_at IS NULL``).

    Uso::

        repo = BaseRepository(MiModelo)
        obj = await repo.get(id=x, tenant_id=tid, session=session)
    """

    def __init__(self, model: type[T]) -> None:
        self.model = model

    async def get(
        self,
        *,
        id: UUID,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> T | None:
        """Retorna un registro por ID y tenant, o ``None`` si no existe
        o fue soft-deleteado."""
        stmt = select(self.model).where(
            self.model.id == id,                # type: ignore[attr-defined]
            self.model.tenant_id == tenant_id,   # type: ignore[attr-defined]
            self.model.deleted_at.is_(None),     # type: ignore[attr-defined]
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> list[T]:
        """Retorna todos los registros activos de un tenant."""
        stmt = (
            select(self.model)
            .where(
                self.model.tenant_id == tenant_id,  # type: ignore[attr-defined]
                self.model.deleted_at.is_(None),     # type: ignore[attr-defined]
            )
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, *, obj: T, session: AsyncSession) -> T:
        """Persiste un nuevo registro y lo retorna con sus valores generados."""
        session.add(obj)
        await session.flush()
        await session.refresh(obj)
        return obj

    async def soft_delete(
        self,
        *,
        id: UUID,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> bool:
        """Marca un registro como eliminado (soft-delete).

        Retorna ``True`` si se eliminó algún registro, ``False`` si no
        se encontró el ID para el tenant indicado.
        """
        stmt = (
            update(self.model)
            .where(
                self.model.id == id,              # type: ignore[attr-defined]
                self.model.tenant_id == tenant_id, # type: ignore[attr-defined]
            )
            .values(deleted_at=func.now())
            .returning(self.model.id)              # type: ignore[attr-defined]
        )
        result = await session.execute(stmt)
        await session.flush()
        return result.scalar_one_or_none() is not None
