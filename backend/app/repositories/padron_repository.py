"""PadronRepository — acceso a datos para VersionPadron y EntradaPadron.

Operaciones de solo lectura y escritura sobre el padrón versionado.
El cifrado/descifrado de email se maneja a nivel de service/repository.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import encryption_service
from app.models.padron import EntradaPadron, VersionPadron
from app.repositories.base import BaseRepository


class VersionPadronRepository(BaseRepository[VersionPadron]):
    """Repositorio para VersionPadron."""

    def __init__(self) -> None:
        super().__init__(VersionPadron)

    async def get_version_activa(
        self,
        *,
        tenant_id: UUID,
        materia_id: UUID,
        cohorte_id: UUID,
        session: AsyncSession,
    ) -> VersionPadron | None:
        """Retorna la versión activa para (tenant, materia, cohorte).

        Args:
            tenant_id: UUID del tenant.
            materia_id: UUID de la materia.
            cohorte_id: UUID de la cohorte.
            session: Sesión async de SQLAlchemy.

        Returns:
            La VersionPadron activa, o None si no existe o está soft-deleteada.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.tenant_id == tenant_id,  # type: ignore[attr-defined]
                self.model.materia_id == materia_id,  # type: ignore[attr-defined]
                self.model.cohorte_id == cohorte_id,  # type: ignore[attr-defined]
                self.model.activa.is_(True),  # type: ignore[attr-defined]
                self.model.deleted_at.is_(None),  # type: ignore[attr-defined]
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_versiones(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        materia_id: UUID | None = None,
        cohorte_id: UUID | None = None,
    ) -> list[VersionPadron]:
        """Lista versiones del tenant con filtros opcionales.

        Args:
            tenant_id: UUID del tenant.
            session: Sesión async.
            materia_id: Filtrar por materia (opcional).
            cohorte_id: Filtrar por cohorte (opcional).

        Returns:
            Lista de VersionPadron ordenada por created_at desc.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.tenant_id == tenant_id,  # type: ignore[attr-defined]
                self.model.deleted_at.is_(None),  # type: ignore[attr-defined]
            )
        )
        if materia_id is not None:
            stmt = stmt.where(self.model.materia_id == materia_id)  # type: ignore[attr-defined]
        if cohorte_id is not None:
            stmt = stmt.where(self.model.cohorte_id == cohorte_id)  # type: ignore[attr-defined]

        stmt = stmt.order_by(self.model.created_at.desc())  # type: ignore[attr-defined]
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def activar_version(
        self,
        *,
        tenant_id: UUID,
        materia_id: UUID,
        cohorte_id: UUID,
        origen: str,
        total_entradas: int,
        session: AsyncSession,
    ) -> VersionPadron:
        """Crea una nueva versión activa, desactivando la anterior si existe.

        Opera en una transacción: desactiva la versión activa previa (si
        existe), luego crea y retorna la nueva versión como activa.

        Args:
            tenant_id: UUID del tenant.
            materia_id: UUID de la materia.
            cohorte_id: UUID de la cohorte.
            origen: Origen de la carga ('archivo' | 'moodle' | 'manual').
            total_entradas: Cantidad de entradas en esta versión.
            session: Sesión async.

        Returns:
            La nueva VersionPadron creada.
        """
        # Desactivar versión anterior si existe
        await self.desactivar_version(
            tenant_id=tenant_id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            session=session,
        )

        # Crear nueva versión activa
        nueva = VersionPadron(
            tenant_id=tenant_id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            activa=True,
            total_entradas=total_entradas,
            origen=origen,
        )
        session.add(nueva)
        await session.flush()
        await session.refresh(nueva)
        return nueva

    async def desactivar_version(
        self,
        *,
        tenant_id: UUID,
        materia_id: UUID,
        cohorte_id: UUID,
        session: AsyncSession,
    ) -> bool:
        """Marca como inactiva la versión activa de la tupla.

        Args:
            tenant_id: UUID del tenant.
            materia_id: UUID de la materia.
            cohorte_id: UUID de la cohorte.
            session: Sesión async.

        Returns:
            True si se desactivó alguna versión, False si no había activa.
        """
        stmt = (
            update(self.model)
            .where(
                self.model.tenant_id == tenant_id,  # type: ignore[attr-defined]
                self.model.materia_id == materia_id,  # type: ignore[attr-defined]
                self.model.cohorte_id == cohorte_id,  # type: ignore[attr-defined]
                self.model.activa.is_(True),  # type: ignore[attr-defined]
                self.model.deleted_at.is_(None),  # type: ignore[attr-defined]
            )
            .values(activa=False)
            .returning(self.model.id)  # type: ignore[attr-defined]
        )
        result = await session.execute(stmt)
        await session.flush()
        return result.scalar_one_or_none() is not None

    async def soft_delete_version(
        self,
        *,
        version_id: UUID,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> bool:
        """Soft-deletea una versión de padrón (vaciar).

        Preserva las entradas (no se borran). La versión queda inactiva
        y con deleted_at seteado.

        Args:
            version_id: UUID de la versión a eliminar.
            tenant_id: UUID del tenant.
            session: Sesión async.

        Returns:
            True si se eliminó, False si no se encontró.
        """
        stmt = (
            update(self.model)
            .where(
                self.model.id == version_id,  # type: ignore[attr-defined]
                self.model.tenant_id == tenant_id,  # type: ignore[attr-defined]
                self.model.deleted_at.is_(None),  # type: ignore[attr-defined]
            )
            .values(
                activa=False,
                deleted_at=func.now(),
            )
            .returning(self.model.id)  # type: ignore[attr-defined]
        )
        result = await session.execute(stmt)
        await session.flush()
        return result.scalar_one_or_none() is not None


class EntradaPadronRepository(BaseRepository[EntradaPadron]):
    """Repositorio para EntradaPadron con manejo de cifrado de email."""

    def __init__(self) -> None:
        super().__init__(EntradaPadron)

    async def get_entradas_by_version(
        self,
        *,
        version_padron_id: UUID,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> list[EntradaPadron]:
        """Retorna todas las entradas de una versión, scoped al tenant.

        Los emails se devuelven desencriptados.

        Args:
            version_padron_id: UUID de la versión.
            tenant_id: UUID del tenant.
            session: Sesión async.

        Returns:
            Lista de EntradaPadron con emails desencriptados.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.version_padron_id == version_padron_id,  # type: ignore[attr-defined]
                self.model.tenant_id == tenant_id,  # type: ignore[attr-defined]
                self.model.deleted_at.is_(None),  # type: ignore[attr-defined]
            )
            .order_by(self.model.created_at.asc())  # type: ignore[attr-defined]
        )
        result = await session.execute(stmt)
        entradas = list(result.scalars().all())
        # Desencriptar emails
        for e in entradas:
            e.email_encrypted = encryption_service.decrypt(e.email_encrypted)  # type: ignore[assignment]
        return entradas

    async def bulk_insert(
        self,
        *,
        entradas: list[EntradaPadron],
        session: AsyncSession,
    ) -> list[EntradaPadron]:
        """Inserta múltiples entradas en una transacción.

        Los emails deben venir cifrados antes de llamar a este método.

        Args:
            entradas: Lista de entradas a insertar.
            session: Sesión async.

        Returns:
            Lista de entradas insertadas con sus IDs generados.
        """
        if not entradas:
            return []
        for e in entradas:
            session.add(e)
        await session.flush()
        for e in entradas:
            await session.refresh(e)
        return entradas
