"""TareaService — núcleo de reglas de negocio del módulo de tareas internas.

Máquina de estados, alcance por rol, trazabilidad de delegación y auditoría.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditCodes, AuditContext, audit_action
from app.models.tarea import EstadoTarea, Tarea
from app.repositories.tarea_repository import TareaRepository
from app.repositories.user_repository import UserRepository
from app.schemas.tarea import TareaCreate, TareaDelegar, TareaCambiarEstado, TareaFiltros


class TareaError(Exception):
    """Error de dominio en operaciones de tarea.

    Attributes:
        status_code: Código HTTP (400, 403, 404).
        detail: Descripción del error.
    """

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class TareaService:
    """Servicio de tareas internas con máquina de estados y alcance por rol.

    Dependencias:
        - TareaRepository: persistencia de tareas.
        - UserRepository: validación de usuarios cross-tenant.
    """

    # Máquina de estados (D-02): estado_actual → set de estados válidos
    _TRANSICIONES: dict[EstadoTarea, set[EstadoTarea]] = {
        EstadoTarea.Pendiente: {EstadoTarea.EnProgreso, EstadoTarea.Cancelada},
        EstadoTarea.EnProgreso: {EstadoTarea.Resuelta, EstadoTarea.Cancelada, EstadoTarea.Pendiente},
        EstadoTarea.Resuelta: {EstadoTarea.EnProgreso},  # reapertura controlada
        EstadoTarea.Cancelada: set(),  # terminal
    }

    def __init__(
        self,
        tarea_repo: TareaRepository | None = None,
        user_repo: UserRepository | None = None,
    ) -> None:
        self._repo = tarea_repo or TareaRepository()
        self._user_repo = user_repo or UserRepository()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _alcance_global(scope: str) -> bool:
        """Determina si el alcance del permiso es global."""
        return scope == "global"

    async def _validar_usuario_en_tenant(
        self,
        usuario_id: UUID,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> None:
        """Valida que un usuario pertenezca al tenant.

        Raises:
            TareaError 400: si el usuario no existe en el tenant.
        """
        usuario = await self._user_repo.get(
            id=usuario_id,
            tenant_id=tenant_id,
            session=session,
        )
        if usuario is None:
            raise TareaError(
                status_code=400,
                detail="User not found in this tenant",
            )

    async def _get_tarea_accesible(
        self,
        tenant_id: UUID,
        tarea_id: UUID,
        scope_user_id: UUID | None,
        session: AsyncSession,
    ) -> Tarea:
        """Obtiene una tarea verificando alcance.

        Si scope_user_id no es None (alcance propio), solo retorna la tarea
        si el usuario es ``asignado_a`` o ``asignado_por``.

        Raises:
            TareaError 404: si no existe, está soft-deleteada o fuera de alcance.
        """
        tarea = await self._repo.get(
            id=tarea_id,
            tenant_id=tenant_id,
            session=session,
        )
        if tarea is None:
            raise TareaError(status_code=404, detail="Tarea not found")

        if scope_user_id is not None:
            if tarea.asignado_a != scope_user_id and tarea.asignado_por != scope_user_id:
                raise TareaError(status_code=404, detail="Tarea not found")

        return tarea

    # ------------------------------------------------------------------
    # Operaciones de dominio
    # ------------------------------------------------------------------

    async def create(
        self,
        *,
        tenant_id: UUID,
        asignado_por: UUID,
        data: TareaCreate,
        session: AsyncSession,
        audit_ctx: AuditContext | None = None,
    ) -> Tarea:
        """Crea una nueva tarea.

        Args:
            tenant_id: UUID del tenant.
            asignado_por: UUID del usuario que asigna (de la sesión).
            data: Datos de creación (TareaCreate).
            session: Sesión async.
            audit_ctx: Contexto de auditoría (opcional; si se pasa, audita).

        Returns:
            La Tarea creada con estado Pendiente.

        Raises:
            TareaError 400: si ``asignado_a`` no pertenece al tenant.
        """
        await self._validar_usuario_en_tenant(
            usuario_id=data.asignado_a,
            tenant_id=tenant_id,
            session=session,
        )

        tarea = Tarea(
            tenant_id=tenant_id,
            asignado_a=data.asignado_a,
            asignado_por=asignado_por,
            descripcion=data.descripcion,
            materia_id=data.materia_id,
            contexto_id=data.contexto_id,
            estado=EstadoTarea.Pendiente,
        )
        created = await self._repo.create(obj=tarea, session=session)

        if audit_ctx is not None:
            await audit_action(
                ctx=audit_ctx,
                accion=AuditCodes.TAREA_CREAR,
                detalle={
                    "tarea_id": str(created.id),
                    "asignado_a": str(created.asignado_a),
                    "asignado_por": str(created.asignado_por),
                    "materia_id": str(created.materia_id) if created.materia_id else None,
                },
                session=session,
                materia_id=created.materia_id,
            )

        return created

    async def delegar(
        self,
        *,
        tenant_id: UUID,
        tarea_id: UUID,
        nuevo_asignado_a: UUID,
        actor: UUID,
        scope: str = "propio",
        session: AsyncSession,
        audit_ctx: AuditContext | None = None,
    ) -> Tarea:
        """Delega/re-asigna una tarea a otro usuario.

        Actualiza ``asignado_a`` y ``asignado_por`` con trazabilidad.

        Args:
            tenant_id: UUID del tenant.
            tarea_id: UUID de la tarea a delegar.
            nuevo_asignado_a: UUID del nuevo usuario asignado.
            actor: UUID del usuario que ejecuta la delegación.
            scope: Alcance del permiso ("global" o "propio").
            session: Sesión async.
            audit_ctx: Contexto de auditoría (opcional).

        Returns:
            La Tarea actualizada.

        Raises:
            TareaError 400: si el nuevo asignado no pertenece al tenant.
            TareaError 404: si la tarea no existe o fuera de alcance.
        """
        scope_user_id = None if self._alcance_global(scope) else actor
        tarea = await self._get_tarea_accesible(
            tenant_id=tenant_id,
            tarea_id=tarea_id,
            scope_user_id=scope_user_id,
            session=session,
        )

        await self._validar_usuario_en_tenant(
            usuario_id=nuevo_asignado_a,
            tenant_id=tenant_id,
            session=session,
        )

        anterior_asignado_a = tarea.asignado_a
        tarea.asignado_a = nuevo_asignado_a
        tarea.asignado_por = actor
        await session.flush()
        await session.refresh(tarea)

        if audit_ctx is not None:
            await audit_action(
                ctx=audit_ctx,
                accion=AuditCodes.TAREA_DELEGAR,
                detalle={
                    "tarea_id": str(tarea_id),
                    "anterior_asignado_a": str(anterior_asignado_a),
                    "nuevo_asignado_a": str(nuevo_asignado_a),
                    "nuevo_asignado_por": str(actor),
                },
                session=session,
                materia_id=tarea.materia_id,
            )

        return tarea

    async def cambiar_estado(
        self,
        *,
        tenant_id: UUID,
        tarea_id: UUID,
        nuevo_estado: EstadoTarea,
        actor: UUID,
        scope: str = "propio",
        session: AsyncSession,
        audit_ctx: AuditContext | None = None,
    ) -> Tarea:
        """Cambia el estado de una tarea validando la máquina de estados.

        Args:
            tenant_id: UUID del tenant.
            tarea_id: UUID de la tarea.
            nuevo_estado: Estado destino.
            actor: UUID del usuario que ejecuta el cambio.
            scope: Alcance del permiso ("global" o "propio").
            session: Sesión async.
            audit_ctx: Contexto de auditoría (opcional).

        Returns:
            La Tarea con el nuevo estado.

        Raises:
            TareaError 400: si la transición no está en la máquina de estados.
            TareaError 403: si alcance "propio" intenta reabrir (Resuelta→EnProgreso).
            TareaError 404: si la tarea no existe o fuera de alcance.
        """
        scope_user_id = None if self._alcance_global(scope) else actor
        tarea = await self._get_tarea_accesible(
            tenant_id=tenant_id,
            tarea_id=tarea_id,
            scope_user_id=scope_user_id,
            session=session,
        )

        # SQLAlchemy devuelve el string de la columna; lo convertimos a Enum
        estado_anterior = EstadoTarea(tarea.estado)
        transiciones_validas = self._TRANSICIONES.get(estado_anterior, set())

        if nuevo_estado not in transiciones_validas:
            raise TareaError(
                status_code=400,
                detail=(
                    f"Invalid transition from {estado_anterior.value} "
                    f"to {nuevo_estado.value}"
                ),
            )

        # Reapertura (Resuelta→EnProgreso) solo para alcance global
        if (
            estado_anterior == EstadoTarea.Resuelta
            and nuevo_estado == EstadoTarea.EnProgreso
            and not self._alcance_global(scope)
        ):
            raise TareaError(
                status_code=403,
                detail="Only coordinators and admins can reopen resolved tasks",
            )

        tarea.estado = nuevo_estado
        await session.flush()
        await session.refresh(tarea)

        if audit_ctx is not None:
            await audit_action(
                ctx=audit_ctx,
                accion=AuditCodes.TAREA_CAMBIAR_ESTADO,
                detalle={
                    "tarea_id": str(tarea_id),
                    "estado_anterior": estado_anterior.value,
                    "estado_nuevo": nuevo_estado.value,
                },
                session=session,
                materia_id=tarea.materia_id,
            )

        return tarea

    async def get(
        self,
        *,
        tenant_id: UUID,
        tarea_id: UUID,
        scope_user_id: UUID | None = None,
        session: AsyncSession,
    ) -> Tarea:
        """Obtiene una tarea por ID.

        Args:
            tenant_id: UUID del tenant.
            tarea_id: UUID de la tarea.
            scope_user_id: Si se pasa, restringe a tareas propias.
            session: Sesión async.

        Returns:
            La Tarea solicitada.

        Raises:
            TareaError 404: si no existe o fuera de alcance.
        """
        return await self._get_tarea_accesible(
            tenant_id=tenant_id,
            tarea_id=tarea_id,
            scope_user_id=scope_user_id,
            session=session,
        )

    async def list(
        self,
        *,
        tenant_id: UUID,
        filtros: TareaFiltros,
        scope_user_id: UUID | None = None,
        session: AsyncSession,
    ) -> list[Tarea]:
        """Lista tareas con filtros opcionales y alcance por rol.

        Args:
            tenant_id: UUID del tenant.
            filtros: Filtros de la consulta (TareaFiltros).
            scope_user_id: Si se pasa (PROFESOR), restringe a tareas propias.
            session: Sesión async.

        Returns:
            Lista de Tareas.
        """
        # Si el usuario tiene roles globales, no aplicamos scope_user_id en filtro
        return await self._repo.list_filtered(
            tenant_id=tenant_id,
            session=session,
            asignado_a=filtros.asignado_a,
            asignado_por=filtros.asignado_por,
            materia_id=filtros.materia_id,
            estado=filtros.estado,
            q=filtros.q,
            scope_user_id=scope_user_id,
        )

    async def list_mias(
        self,
        *,
        tenant_id: UUID,
        usuario_id: UUID,
        session: AsyncSession,
    ) -> list[Tarea]:
        """Retorna las tareas asignadas al usuario (``asignado_a``).

        Args:
            tenant_id: UUID del tenant.
            usuario_id: UUID del usuario autenticado.
            session: Sesión async.

        Returns:
            Lista de Tareas donde ``asignado_a == usuario_id``.
        """
        return await self._repo.list_mias(
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            session=session,
        )

    async def delete(
        self,
        *,
        tenant_id: UUID,
        tarea_id: UUID,
        session: AsyncSession,
    ) -> bool:
        """Soft-delete de una tarea.

        Args:
            tenant_id: UUID del tenant.
            tarea_id: UUID de la tarea a eliminar.
            session: Sesión async.

        Returns:
            True si se eliminó, False si no se encontró.
        """
        return await self._repo.soft_delete(
            id=tarea_id,
            tenant_id=tenant_id,
            session=session,
        )
