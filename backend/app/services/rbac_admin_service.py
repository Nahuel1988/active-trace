"""RbacAdminService — administración del catálogo de permisos y la matriz rol × permiso.

Uso::

    from app.services.rbac_admin_service import RbacAdminService

    service = RbacAdminService()
    permisos = await service.listar_permisos(tenant_id=..., session=db)
    matriz = await service.listar_matriz(tenant_id=..., session=db)
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permiso import Permiso, RolPermiso
from app.models.role import Role
from app.repositories.permiso_repository import PermisoRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.rol_permiso_repository import RolPermisoRepository


class RbacError(Exception):
    """Excepción de dominio para errores de administración RBAC.

    Attributes:
        status_code: Código HTTP sugerido (400, 404, 409).
        detail: Mensaje descriptivo.
    """

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class RbacAdminService:
    """Servicio de administración del catálogo RBAC.

    Dependencias:
        - PermisoRepository
        - RoleRepository
        - RolPermisoRepository
    """

    def __init__(
        self,
        permiso_repo: PermisoRepository | None = None,
        role_repo: RoleRepository | None = None,
        rol_permiso_repo: RolPermisoRepository | None = None,
    ) -> None:
        self._permiso_repo = permiso_repo or PermisoRepository()
        self._role_repo = role_repo or RoleRepository()
        self._rol_permiso_repo = rol_permiso_repo or RolPermisoRepository()

    # ── Permisos ───────────────────────────────────────────────────────

    async def crear_permiso(
        self,
        *,
        tenant_id: UUID,
        modulo: str,
        accion: str,
        session: AsyncSession,
        asignado_por: UUID | None = None,
    ) -> Permiso:
        """Crea un nuevo permiso en el catálogo del tenant.

        Args:
            tenant_id: UUID del tenant.
            modulo: Módulo funcional.
            accion: Acción dentro del módulo.
            session: Sesión de base de datos async.
            asignado_por: UUID del creador (para tracking).

        Returns:
            El ``Permiso`` creado.

        Raises:
            RbacError: 409 si el permiso ya existe (code duplicado).
        """
        code = f"{modulo}:{accion}"

        existente = await self._permiso_repo.get_by_code(
            tenant_id=tenant_id,
            code=code,
            session=session,
        )
        if existente is not None:
            msg = f"El permiso '{code}' ya existe en este tenant"
            raise RbacError(status_code=409, detail=msg)

        permiso = Permiso(
            tenant_id=tenant_id,
            modulo=modulo,
            accion=accion,
            code=code,
        )
        return await self._permiso_repo.create(obj=permiso, session=session)

    async def listar_permisos(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> list[Permiso]:
        """Lista todos los permisos activos de un tenant."""
        return await self._permiso_repo.list(tenant_id=tenant_id, session=session)

    async def obtener_permiso_por_code(
        self,
        *,
        tenant_id: UUID,
        code: str,
        session: AsyncSession,
    ) -> Permiso | None:
        """Busca un permiso por code dentro del tenant."""
        return await self._permiso_repo.get_by_code(
            tenant_id=tenant_id,
            code=code,
            session=session,
        )

    async def eliminar_permiso(
        self,
        *,
        tenant_id: UUID,
        permiso_id: UUID,
        session: AsyncSession,
    ) -> bool:
        """Elimina (soft-delete) un permiso del catálogo.

        Returns:
            ``True`` si se eliminó, ``False`` si no existía.
        """
        return await self._permiso_repo.soft_delete(
            id=permiso_id,
            tenant_id=tenant_id,
            session=session,
        )

    # ── Roles ──────────────────────────────────────────────────────────

    async def listar_roles(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> list[Role]:
        """Lista todos los roles activos de un tenant."""
        return await self._role_repo.list(tenant_id=tenant_id, session=session)

    async def obtener_rol_por_code(
        self,
        *,
        tenant_id: UUID,
        code: str,
        session: AsyncSession,
    ) -> Role | None:
        """Busca un rol por code dentro del tenant."""
        return await self._role_repo.get_by_code(
            tenant_id=tenant_id,
            code=code,
            session=session,
        )

    # ── Matriz ─────────────────────────────────────────────────────────

    async def asignar_permiso_a_rol(
        self,
        *,
        tenant_id: UUID,
        role_code: str,
        permiso_code: str,
        scope: str,
        session: AsyncSession,
        asignado_por: UUID | None = None,
    ) -> RolPermiso:
        """Asigna un permiso a un rol con el scope indicado.

        Args:
            tenant_id: UUID del tenant.
            role_code: Código del rol (ej: ``profesor``).
            permiso_code: Código del permiso (ej: ``comunicacion:enviar``).
            scope: Alcance — ``"global"`` o ``"propio"``.
            session: Sesión de base de datos async.
            asignado_por: UUID del administrador que asigna.

        Returns:
            La fila ``RolPermiso`` creada o actualizada.

        Raises:
            RbacError: 404 si el rol o el permiso no existen en el tenant.
        """
        role = await self._role_repo.get_by_code(
            tenant_id=tenant_id,
            code=role_code,
            session=session,
        )
        if role is None:
            msg = f"Rol '{role_code}' no encontrado en este tenant"
            raise RbacError(status_code=404, detail=msg)

        permiso = await self._permiso_repo.get_by_code(
            tenant_id=tenant_id,
            code=permiso_code,
            session=session,
        )
        if permiso is None:
            msg = f"Permiso '{permiso_code}' no encontrado en este tenant"
            raise RbacError(status_code=404, detail=msg)

        return await self._rol_permiso_repo.asignar(
            tenant_id=tenant_id,
            role_id=role.id,
            permiso_id=permiso.id,
            scope=scope,
            session=session,
            asignado_por=asignado_por,
        )

    async def quitar_permiso_a_rol(
        self,
        *,
        tenant_id: UUID,
        role_code: str,
        permiso_code: str,
        session: AsyncSession,
    ) -> bool:
        """Quita un permiso de un rol.

        Args:
            tenant_id: UUID del tenant.
            role_code: Código del rol.
            permiso_code: Código del permiso.
            session: Sesión de base de datos async.

        Returns:
            ``True`` si se eliminó, ``False`` si no existía.
        """
        role = await self._role_repo.get_by_code(
            tenant_id=tenant_id,
            code=role_code,
            session=session,
        )
        if role is None:
            return False

        permiso = await self._permiso_repo.get_by_code(
            tenant_id=tenant_id,
            code=permiso_code,
            session=session,
        )
        if permiso is None:
            return False

        return await self._rol_permiso_repo.quitar(
            tenant_id=tenant_id,
            role_id=role.id,
            permiso_id=permiso.id,
            session=session,
        )

    async def listar_matriz(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> list[dict]:
        """Retorna la matriz completa rol × permiso del tenant.

        Returns:
            Lista de dicts con datos desnormalizados: role_code, role_nombre,
            permiso_code, scope.
        """
        stmt = (
            select(
                Role.code.label("role_code"),
                Role.nombre.label("role_nombre"),
                Permiso.code.label("permiso_code"),
                RolPermiso.scope,
            )
            .select_from(RolPermiso)
            .join(Role, Role.id == RolPermiso.role_id)
            .join(Permiso, Permiso.id == RolPermiso.permiso_id)
            .where(RolPermiso.tenant_id == tenant_id)
            .order_by(Role.code, Permiso.code)
        )
        result = await session.execute(stmt)
        rows = result.fetchall()
        return [
            {
                "role_code": row.role_code,
                "role_nombre": row.role_nombre,
                "permiso_code": row.permiso_code,
                "scope": row.scope,
            }
            for row in rows
        ]
