"""RolPermisoRepository — operaciones de acceso a datos para RolPermiso.

RolPermiso tiene PK compuesta (tenant_id, role_id, permiso_id) y NO
hereda de TenantScopedMixin, por lo que se implementan operaciones
custom en lugar de usar BaseRepository.
"""

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permiso import RolPermiso


class RolPermisoRepository:
    """Repositorio para la matriz RolPermiso.

    Métodos:
        asignar: crea una fila rol ↔ permiso.
        quitar: elimina una fila rol ↔ permiso.
        listar_por_tenant: devuelve toda la matriz de un tenant.
        listar_por_rol: devuelve los permisos de un rol específico.
    """

    async def asignar(
        self,
        *,
        tenant_id: UUID,
        role_id: UUID,
        permiso_id: UUID,
        scope: str,
        session: AsyncSession,
        asignado_por: UUID | None = None,
    ) -> RolPermiso:
        """Asigna un permiso a un rol.

        Crea una fila ``RolPermiso``. Si ya existe (misma PK), la
        actualiza (upsert).

        Args:
            tenant_id: UUID del tenant.
            role_id: UUID del rol.
            permiso_id: UUID del permiso.
            scope: Alcance — ``"global"`` o ``"propio"``.
            session: Sesión de base de datos async.
            asignado_por: UUID del usuario que hace la asignación (auditoría).

        Returns:
            La instancia ``RolPermiso`` creada o actualizada.
        """
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        stmt = pg_insert(RolPermiso).values(
            tenant_id=tenant_id,
            role_id=role_id,
            permiso_id=permiso_id,
            scope=scope,
            asignado_por=asignado_por,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["tenant_id", "role_id", "permiso_id"],
            set_={"scope": scope, "asignado_por": asignado_por},
        )
        stmt = stmt.returning(RolPermiso)

        result = await session.execute(stmt)
        await session.flush()
        return result.scalar_one()

    async def quitar(
        self,
        *,
        tenant_id: UUID,
        role_id: UUID,
        permiso_id: UUID,
        session: AsyncSession,
    ) -> bool:
        """Quita un permiso de un rol (elimina la fila).

        Args:
            tenant_id: UUID del tenant.
            role_id: UUID del rol.
            permiso_id: UUID del permiso.
            session: Sesión de base de datos async.

        Returns:
            ``True`` si se eliminó alguna fila, ``False`` si no existía.
        """
        stmt = delete(RolPermiso).where(
            RolPermiso.tenant_id == tenant_id,
            RolPermiso.role_id == role_id,
            RolPermiso.permiso_id == permiso_id,
        )
        result = await session.execute(stmt)
        await session.flush()
        return result.rowcount > 0

    async def listar_por_tenant(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> list[RolPermiso]:
        """Retorna todas las filas de la matriz para un tenant.

        Args:
            tenant_id: UUID del tenant.
            session: Sesión de base de datos async.

        Returns:
            Lista de ``RolPermiso`` del tenant.
        """
        stmt = select(RolPermiso).where(RolPermiso.tenant_id == tenant_id)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def listar_por_rol(
        self,
        *,
        tenant_id: UUID,
        role_id: UUID,
        session: AsyncSession,
    ) -> list[RolPermiso]:
        """Retorna los permisos asignados a un rol específico.

        Args:
            tenant_id: UUID del tenant.
            role_id: UUID del rol.
            session: Sesión de base de datos async.

        Returns:
            Lista de ``RolPermiso`` del rol.
        """
        stmt = select(RolPermiso).where(
            RolPermiso.tenant_id == tenant_id,
            RolPermiso.role_id == role_id,
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
