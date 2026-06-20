"""SalarioPlusRepository — acceso a datos para SalarioPlus."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.salario_plus import SalarioPlus
from app.repositories.base import BaseRepository


class SolapamientoPlusError(Exception):
    """Se lanza cuando una vigencia de plus se solapa con una existente."""


class SalarioPlusRepository(BaseRepository[SalarioPlus]):
    """Repositorio para SalarioPlus con validación de solapamiento de vigencia."""

    def __init__(self) -> None:
        super().__init__(SalarioPlus)

    async def get_vigente(
        self,
        *,
        tenant_id: UUID,
        grupo: str,
        rol: str,
        periodo: str,
        session: AsyncSession,
    ) -> SalarioPlus | None:
        """Retorna el SalarioPlus vigente para (grupo, rol) en un período AAAA-MM."""
        anio, mes = int(periodo[:4]), int(periodo[5:7])
        primer_dia = date(anio, mes, 1)
        stmt = (
            select(self.model)
            .where(
                self.model.tenant_id == tenant_id,
                self.model.grupo == grupo,
                self.model.rol == rol,
                self.model.desde <= primer_dia,
                or_(
                    self.model.hasta.is_(None),
                    self.model.hasta >= primer_dia,
                ),
                self.model.deleted_at.is_(None),
            )
            .order_by(self.model.desde.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_vigentes_por_grupos(
        self,
        *,
        tenant_id: UUID,
        grupos: list[str],
        rol: str,
        periodo: str,
        session: AsyncSession,
    ) -> list[SalarioPlus]:
        """Retorna los SalarioPlus vigentes para una lista de grupos y un rol.

        Implementa PA-23: UNA aplicación por clave (grupo, rol).
        Si hay múltiples vigentes para el mismo (grupo, rol) (no debería por
        validación de solapamiento), se toma el de desde más reciente.
        """
        if not grupos:
            return []
        anio, mes = int(periodo[:4]), int(periodo[5:7])
        primer_dia = date(anio, mes, 1)
        stmt = (
            select(self.model)
            .where(
                self.model.tenant_id == tenant_id,
                self.model.grupo.in_(grupos),
                self.model.rol == rol,
                self.model.desde <= primer_dia,
                or_(
                    self.model.hasta.is_(None),
                    self.model.hasta >= primer_dia,
                ),
                self.model.deleted_at.is_(None),
            )
            .order_by(self.model.grupo, self.model.desde.desc())
        )
        result = await session.execute(stmt)
        rows = list(result.scalars().all())
        # Deduplicar: una por (grupo, rol) — la más reciente ya viene primero
        seen: set[tuple[str, str]] = set()
        deduplicados: list[SalarioPlus] = []
        for row in rows:
            key = (row.grupo, row.rol)
            if key not in seen:
                seen.add(key)
                deduplicados.append(row)
        return deduplicados

    async def list_filtered(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        grupo: str | None = None,
        rol: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[SalarioPlus]:
        """Lista plus activos con filtros opcionales por grupo y rol."""
        stmt = select(self.model).where(
            self.model.tenant_id == tenant_id,
            self.model.deleted_at.is_(None),
        )
        if grupo is not None:
            stmt = stmt.where(self.model.grupo == grupo)
        if rol is not None:
            stmt = stmt.where(self.model.rol == rol)
        stmt = stmt.order_by(self.model.grupo, self.model.rol, self.model.desde.desc())
        stmt = stmt.offset(offset).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def _check_solapamiento(
        self,
        *,
        tenant_id: UUID,
        grupo: str,
        rol: str,
        desde: date,
        hasta: date | None,
        session: AsyncSession,
        exclude_id: UUID | None = None,
    ) -> None:
        """Valida que la vigencia propuesta no se solape con otra del mismo (grupo, rol)."""
        stmt = select(self.model).where(
            self.model.tenant_id == tenant_id,
            self.model.grupo == grupo,
            self.model.rol == rol,
            self.model.deleted_at.is_(None),
            and_(
                self.model.desde <= (hasta if hasta is not None else date(9999, 12, 31)),
                or_(
                    self.model.hasta.is_(None),
                    self.model.hasta >= desde,
                ),
            ),
        )
        if exclude_id is not None:
            stmt = stmt.where(self.model.id != exclude_id)

        result = await session.execute(stmt)
        conflicto = result.scalar_one_or_none()
        if conflicto is not None:
            raise SolapamientoPlusError(
                f"La vigencia solapa con SalarioPlus existente "
                f"(grupo={conflicto.grupo}, rol={conflicto.rol}, "
                f"desde={conflicto.desde}, hasta={conflicto.hasta})"
            )

    async def create(
        self,
        *,
        obj: SalarioPlus,
        session: AsyncSession,
    ) -> SalarioPlus:
        """Crea un SalarioPlus validando solapamiento de vigencia."""
        await self._check_solapamiento(
            tenant_id=obj.tenant_id,
            grupo=obj.grupo,
            rol=obj.rol,
            desde=obj.desde,
            hasta=obj.hasta,
            session=session,
        )
        return await super().create(obj=obj, session=session)

    async def update(
        self,
        *,
        obj: SalarioPlus,
        session: AsyncSession,
    ) -> SalarioPlus:
        """Actualiza un SalarioPlus validando solapamiento (excluyendo a sí mismo)."""
        await self._check_solapamiento(
            tenant_id=obj.tenant_id,
            grupo=obj.grupo,
            rol=obj.rol,
            desde=obj.desde,
            hasta=obj.hasta,
            session=session,
            exclude_id=obj.id,
        )
        await session.flush()
        await session.refresh(obj)
        return obj
