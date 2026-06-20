"""SalarioBaseRepository — acceso a datos para SalarioBase."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.salario_base import SalarioBase
from app.repositories.base import BaseRepository


class SolapamientoVigenciaError(Exception):
    """Se lanza cuando una nueva vigencia se solapa con una existente."""


class SalarioBaseRepository(BaseRepository[SalarioBase]):
    """Repositorio para SalarioBase con validación de solapamiento de vigencia."""

    def __init__(self) -> None:
        super().__init__(SalarioBase)

    async def get_vigente(
        self,
        *,
        tenant_id: UUID,
        rol: str,
        periodo: str,
        session: AsyncSession,
    ) -> SalarioBase | None:
        """Retorna el SalarioBase vigente para un rol en un período AAAA-MM.

        Vigente = desde <= primer día del período AND (hasta IS NULL OR hasta >= último día).
        En la práctica usamos el primer día del mes para la comparación.
        """
        anio, mes = int(periodo[:4]), int(periodo[5:7])
        primer_dia = date(anio, mes, 1)
        stmt = (
            select(self.model)
            .where(
                self.model.tenant_id == tenant_id,
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

    async def list_filtered(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        rol: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[SalarioBase]:
        """Lista salarios base activos con filtro opcional por rol."""
        stmt = select(self.model).where(
            self.model.tenant_id == tenant_id,
            self.model.deleted_at.is_(None),
        )
        if rol is not None:
            stmt = stmt.where(self.model.rol == rol)
        stmt = stmt.order_by(self.model.rol, self.model.desde.desc()).offset(offset).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def _check_solapamiento(
        self,
        *,
        tenant_id: UUID,
        rol: str,
        desde: date,
        hasta: date | None,
        session: AsyncSession,
        exclude_id: UUID | None = None,
    ) -> None:
        """Valida que la vigencia propuesta no se solape con ninguna existente.

        Dos rangos [A_desde, A_hasta] y [B_desde, B_hasta] se solapan cuando:
            A_desde <= B_hasta  AND  B_desde <= A_hasta
        Con hasta NULL = infinito → tratar como fecha muy lejana.
        """
        stmt = select(self.model).where(
            self.model.tenant_id == tenant_id,
            self.model.rol == rol,
            self.model.deleted_at.is_(None),
            # solapamiento: desde_nuevo <= hasta_existente AND desde_existente <= hasta_nuevo
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
            raise SolapamientoVigenciaError(
                f"La vigencia solapa con SalarioBase existente "
                f"(rol={conflicto.rol}, desde={conflicto.desde}, hasta={conflicto.hasta})"
            )

    async def create(
        self,
        *,
        obj: SalarioBase,
        session: AsyncSession,
    ) -> SalarioBase:
        """Crea un SalarioBase validando que no haya solapamiento de vigencia."""
        await self._check_solapamiento(
            tenant_id=obj.tenant_id,
            rol=obj.rol,
            desde=obj.desde,
            hasta=obj.hasta,
            session=session,
        )
        return await super().create(obj=obj, session=session)

    async def update(
        self,
        *,
        obj: SalarioBase,
        session: AsyncSession,
    ) -> SalarioBase:
        """Actualiza un SalarioBase validando solapamiento (excluyendo a sí mismo)."""
        await self._check_solapamiento(
            tenant_id=obj.tenant_id,
            rol=obj.rol,
            desde=obj.desde,
            hasta=obj.hasta,
            session=session,
            exclude_id=obj.id,
        )
        await session.flush()
        await session.refresh(obj)
        return obj
