"""ComentarioTareaService — gestión de comentarios en tareas.

Append-only: los comentarios no se editan ni eliminan.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comentario_tarea import ComentarioTarea
from app.models.tarea import Tarea
from app.repositories.comentario_tarea_repository import ComentarioTareaRepository
from app.repositories.tarea_repository import TareaRepository


class ComentarioError(Exception):
    """Error de dominio en operaciones de comentarios."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class ComentarioTareaService:
    """Servicio de comentarios de tareas (append-only)."""

    def __init__(
        self,
        comentario_repo: ComentarioTareaRepository | None = None,
        tarea_repo: TareaRepository | None = None,
    ) -> None:
        self._repo = comentario_repo or ComentarioTareaRepository()
        self._tarea_repo = tarea_repo or TareaRepository()

    async def _verificar_acceso_tarea(
        self,
        tenant_id: UUID,
        tarea_id: UUID,
        scope_user_id: UUID | None,
        session: AsyncSession,
    ) -> Tarea:
        """Verifica que la tarea exista y sea accesible.

        Args:
            tenant_id: UUID del tenant.
            tarea_id: UUID de la tarea.
            scope_user_id: Si se pasa, restringe a tareas propias.
            session: Sesión async.

        Returns:
            La Tarea si es accesible.

        Raises:
            ComentarioError 404: si no existe o fuera de alcance.
        """
        tarea = await self._tarea_repo.get(
            id=tarea_id,
            tenant_id=tenant_id,
            session=session,
        )
        if tarea is None:
            raise ComentarioError(status_code=404, detail="Tarea not found")

        if scope_user_id is not None:
            if tarea.asignado_a != scope_user_id and tarea.asignado_por != scope_user_id:
                raise ComentarioError(status_code=404, detail="Tarea not found")

        return tarea

    async def crear(
        self,
        *,
        tenant_id: UUID,
        tarea_id: UUID,
        autor_id: UUID,
        texto: str,
        session: AsyncSession,
        scope_user_id: UUID | None = None,
    ) -> ComentarioTarea:
        """Crea un comentario en una tarea.

        Args:
            tenant_id: UUID del tenant.
            tarea_id: UUID de la tarea.
            autor_id: UUID del autor (de la sesión).
            texto: Contenido del comentario.
            session: Sesión async.
            scope_user_id: Si se pasa, verifica acceso propio.

        Returns:
            El ComentarioTarea creado.

        Raises:
            ComentarioError 404: si la tarea no existe o fuera de alcance.
        """
        await self._verificar_acceso_tarea(
            tenant_id=tenant_id,
            tarea_id=tarea_id,
            scope_user_id=scope_user_id,
            session=session,
        )

        comentario = ComentarioTarea(
            tenant_id=tenant_id,
            tarea_id=tarea_id,
            autor_id=autor_id,
            texto=texto,
        )
        return await self._repo.create(obj=comentario, session=session)

    async def listar(
        self,
        *,
        tenant_id: UUID,
        tarea_id: UUID,
        session: AsyncSession,
        scope_user_id: UUID | None = None,
    ) -> list[ComentarioTarea]:
        """Lista los comentarios de una tarea en orden cronológico ascendente.

        Args:
            tenant_id: UUID del tenant.
            tarea_id: UUID de la tarea.
            session: Sesión async.
            scope_user_id: Si se pasa, verifica acceso propio.

        Returns:
            Lista de ComentarioTarea ordenada por creado_at ASC.

        Raises:
            ComentarioError 404: si la tarea no existe o fuera de alcance.
        """
        await self._verificar_acceso_tarea(
            tenant_id=tenant_id,
            tarea_id=tarea_id,
            scope_user_id=scope_user_id,
            session=session,
        )

        return await self._repo.list_by_tarea(
            tenant_id=tenant_id,
            tarea_id=tarea_id,
            session=session,
        )
