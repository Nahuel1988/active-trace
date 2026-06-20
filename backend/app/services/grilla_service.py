"""GrillaService — gestión de la grilla salarial (SalarioBase y SalarioPlus)."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.salario_base import SalarioBase
from app.models.salario_plus import SalarioPlus
from app.repositories.salario_base_repository import (
    SalarioBaseRepository,
    SolapamientoVigenciaError,
)
from app.repositories.salario_plus_repository import (
    SalarioPlusRepository,
    SolapamientoPlusError,
)
from app.schemas.salario_base import SalarioBaseCreate, SalarioBaseUpdate
from app.schemas.salario_plus import SalarioPlusCreate, SalarioPlusUpdate


class GrillaError(Exception):
    """Error de dominio de la grilla salarial."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class GrillaService:
    """Servicio de gestión de grilla salarial.

    Delega toda la persistencia a los repositorios.
    Convierte errores de dominio en GrillaError con código HTTP.
    """

    def __init__(
        self,
        salario_base_repo: SalarioBaseRepository | None = None,
        salario_plus_repo: SalarioPlusRepository | None = None,
    ) -> None:
        self._base_repo = salario_base_repo or SalarioBaseRepository()
        self._plus_repo = salario_plus_repo or SalarioPlusRepository()

    # ─────────────────────────────────────────────────────────────────────
    # SalarioBase
    # ─────────────────────────────────────────────────────────────────────

    async def configurar_salario_base(
        self,
        *,
        tenant_id: UUID,
        data: SalarioBaseCreate,
        session: AsyncSession,
    ) -> SalarioBase:
        """Crea un nuevo SalarioBase con validación de solapamiento de vigencia."""
        obj = SalarioBase(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            rol=data.rol.value,
            monto=data.monto,
            desde=data.desde,
            hasta=data.hasta,
        )
        try:
            return await self._base_repo.create(obj=obj, session=session)
        except SolapamientoVigenciaError as exc:
            raise GrillaError(409, str(exc)) from exc

    async def listar_salarios_base(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        rol: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[SalarioBase]:
        """Lista salarios base activos con paginación y filtro opcional por rol."""
        return await self._base_repo.list_filtered(
            tenant_id=tenant_id,
            session=session,
            rol=rol,
            limit=limit,
            offset=offset,
        )

    async def obtener_base_vigente(
        self,
        *,
        tenant_id: UUID,
        rol: str,
        periodo: str,
        session: AsyncSession,
    ) -> SalarioBase | None:
        """Devuelve el SalarioBase vigente para ese rol en el período AAAA-MM."""
        return await self._base_repo.get_vigente(
            tenant_id=tenant_id,
            rol=rol,
            periodo=periodo,
            session=session,
        )

    async def actualizar_salario_base(
        self,
        *,
        tenant_id: UUID,
        salario_id: UUID,
        data: SalarioBaseUpdate,
        session: AsyncSession,
    ) -> SalarioBase:
        """Actualiza monto y/o hasta de un SalarioBase existente."""
        obj = await self._base_repo.get(id=salario_id, tenant_id=tenant_id, session=session)
        if obj is None:
            raise GrillaError(404, "SalarioBase no encontrado")
        if data.monto is not None:
            obj.monto = data.monto
        if data.hasta is not None:
            obj.hasta = data.hasta
        try:
            return await self._base_repo.update(obj=obj, session=session)
        except SolapamientoVigenciaError as exc:
            raise GrillaError(409, str(exc)) from exc

    async def eliminar_salario_base(
        self,
        *,
        tenant_id: UUID,
        salario_id: UUID,
        session: AsyncSession,
    ) -> None:
        """Soft-delete de un SalarioBase."""
        deleted = await self._base_repo.soft_delete(
            id=salario_id, tenant_id=tenant_id, session=session
        )
        if not deleted:
            raise GrillaError(404, "SalarioBase no encontrado")

    # ─────────────────────────────────────────────────────────────────────
    # SalarioPlus
    # ─────────────────────────────────────────────────────────────────────

    async def configurar_salario_plus(
        self,
        *,
        tenant_id: UUID,
        data: SalarioPlusCreate,
        session: AsyncSession,
    ) -> SalarioPlus:
        """Crea un nuevo SalarioPlus con validación de solapamiento de vigencia."""
        obj = SalarioPlus(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            grupo=data.grupo,
            rol=data.rol,
            descripcion=data.descripcion,
            monto=data.monto,
            desde=data.desde,
            hasta=data.hasta,
        )
        try:
            return await self._plus_repo.create(obj=obj, session=session)
        except SolapamientoPlusError as exc:
            raise GrillaError(409, str(exc)) from exc

    async def listar_salarios_plus(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        grupo: str | None = None,
        rol: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[SalarioPlus]:
        """Lista plus activos con paginación y filtros opcionales."""
        return await self._plus_repo.list_filtered(
            tenant_id=tenant_id,
            session=session,
            grupo=grupo,
            rol=rol,
            limit=limit,
            offset=offset,
        )

    async def obtener_plus_vigentes(
        self,
        *,
        tenant_id: UUID,
        grupos: list[str],
        rol: str,
        periodo: str,
        session: AsyncSession,
    ) -> list[SalarioPlus]:
        """Devuelve lista de SalarioPlus vigentes para esos grupos y rol en el período."""
        return await self._plus_repo.get_vigentes_por_grupos(
            tenant_id=tenant_id,
            grupos=grupos,
            rol=rol,
            periodo=periodo,
            session=session,
        )

    async def actualizar_salario_plus(
        self,
        *,
        tenant_id: UUID,
        plus_id: UUID,
        data: SalarioPlusUpdate,
        session: AsyncSession,
    ) -> SalarioPlus:
        """Actualiza descripción, monto y/o hasta de un SalarioPlus."""
        obj = await self._plus_repo.get(id=plus_id, tenant_id=tenant_id, session=session)
        if obj is None:
            raise GrillaError(404, "SalarioPlus no encontrado")
        if data.descripcion is not None:
            obj.descripcion = data.descripcion
        if data.monto is not None:
            obj.monto = data.monto
        if data.hasta is not None:
            obj.hasta = data.hasta
        try:
            return await self._plus_repo.update(obj=obj, session=session)
        except SolapamientoPlusError as exc:
            raise GrillaError(409, str(exc)) from exc

    async def eliminar_salario_plus(
        self,
        *,
        tenant_id: UUID,
        plus_id: UUID,
        session: AsyncSession,
    ) -> None:
        """Soft-delete de un SalarioPlus."""
        deleted = await self._plus_repo.soft_delete(
            id=plus_id, tenant_id=tenant_id, session=session
        )
        if not deleted:
            raise GrillaError(404, "SalarioPlus no encontrado")
