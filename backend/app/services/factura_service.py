"""FacturaService — gestión de facturas de docentes monotributistas."""

from __future__ import annotations

import uuid
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.factura import EstadoFactura, Factura
from app.repositories.factura_repository import FacturaRepository
from app.repositories.user_repository import UserRepository
from app.schemas.factura import FacturaCreate, FacturaResponse, FacturaUpdate


class FacturaError(Exception):
    """Error de dominio del servicio de facturas."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class FacturaService:
    """Servicio para gestión de facturas de monotributistas.

    Reglas de dominio (D7):
    - Solo docentes con facturador=True pueden tener facturas.
    - Transición Pendiente → Abonada (solo forward; no borrado).
    - Una Factura Abonada es inmutable.
    """

    def __init__(
        self,
        factura_repo: FacturaRepository | None = None,
        user_repo: UserRepository | None = None,
    ) -> None:
        self._repo = factura_repo or FacturaRepository()
        self._user_repo = user_repo or UserRepository()

    async def crear_factura(
        self,
        *,
        tenant_id: UUID,
        data: FacturaCreate,
        session: AsyncSession,
    ) -> FacturaResponse:
        """Crea una factura validando que el usuario sea facturador."""
        user = await self._user_repo.get(
            id=data.usuario_id, tenant_id=tenant_id, session=session
        )
        if user is None:
            raise FacturaError(404, "Usuario no encontrado")
        if not user.facturador:
            raise FacturaError(
                422, "El usuario no tiene habilitada la facturación"
            )

        factura = Factura(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            usuario_id=data.usuario_id,
            periodo=data.periodo,
            detalle=data.detalle,
            referencia_archivo=data.referencia_archivo,
            tamano_kb=data.tamano_kb,
            estado=EstadoFactura.Pendiente.value,
        )
        creada = await self._repo.create(obj=factura, session=session)
        return FacturaResponse.model_validate(creada)

    async def listar_facturas(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        periodo: str | None = None,
        estado: str | None = None,
        usuario_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FacturaResponse]:
        """Lista facturas con filtros opcionales."""
        facturas = await self._repo.list_filtered(
            tenant_id=tenant_id,
            session=session,
            periodo=periodo,
            estado=estado,
            usuario_id=usuario_id,
            limit=limit,
            offset=offset,
        )
        return [FacturaResponse.model_validate(f) for f in facturas]

    async def obtener_factura(
        self,
        *,
        tenant_id: UUID,
        factura_id: UUID,
        session: AsyncSession,
    ) -> FacturaResponse:
        """Obtiene una factura por ID."""
        factura = await self._repo.get(id=factura_id, tenant_id=tenant_id, session=session)
        if factura is None:
            raise FacturaError(404, "Factura no encontrada")
        return FacturaResponse.model_validate(factura)

    async def actualizar_factura(
        self,
        *,
        tenant_id: UUID,
        factura_id: UUID,
        data: FacturaUpdate,
        session: AsyncSession,
    ) -> FacturaResponse:
        """Actualiza una Factura solo si está en estado Pendiente."""
        factura = await self._repo.get(id=factura_id, tenant_id=tenant_id, session=session)
        if factura is None:
            raise FacturaError(404, "Factura no encontrada")
        if factura.estado != EstadoFactura.Pendiente.value:
            raise FacturaError(409, "Solo se puede editar una Factura en estado Pendiente")

        if data.detalle is not None:
            factura.detalle = data.detalle
        if data.referencia_archivo is not None:
            factura.referencia_archivo = data.referencia_archivo
        if data.tamano_kb is not None:
            factura.tamano_kb = data.tamano_kb

        actualizada = await self._repo.update_pendiente(obj=factura, session=session)
        return FacturaResponse.model_validate(actualizada)

    async def abonar(
        self,
        *,
        tenant_id: UUID,
        factura_id: UUID,
        session: AsyncSession,
    ) -> FacturaResponse:
        """Transiciona una Factura de Pendiente a Abonada.

        Reglas:
        - Solo Pendiente → Abonada.
        - Abonar una Abonada lanza FacturaError 409.
        """
        # Verificar que existe
        factura = await self._repo.get(id=factura_id, tenant_id=tenant_id, session=session)
        if factura is None:
            raise FacturaError(404, "Factura no encontrada")

        filas = await self._repo.abonar(
            tenant_id=tenant_id, factura_id=factura_id, session=session
        )
        if filas == 0:
            raise FacturaError(409, "La factura ya está Abonada o no se puede pagar")

        await session.refresh(factura)
        return FacturaResponse.model_validate(factura)
