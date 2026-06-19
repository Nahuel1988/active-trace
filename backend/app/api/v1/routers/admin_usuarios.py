"""Router admin_usuarios — ABM de usuarios del tenant con PII descifrada.

Endpoints protegidos por el permiso 'usuarios:gestionar'.
La identidad del caller se deriva SIEMPRE del JWT verificado.
PII descifrada SOLO en responses de este router (no en otros endpoints).

GET    /api/v1/admin/usuarios
GET    /api/v1/admin/usuarios/{id}
POST   /api/v1/admin/usuarios
PUT    /api/v1/admin/usuarios/{id}
DELETE /api/v1/admin/usuarios/{id}
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import PermissionGrant, require_permission
from app.schemas.usuario import UsuarioCreate, UsuarioResponse, UsuarioUpdate
from app.services.usuario_service import UsuarioService, UsuarioServiceError

router = APIRouter(
    prefix="/api/v1/admin/usuarios",
    tags=["admin-usuarios"],
)


def _get_service() -> UsuarioService:
    return UsuarioService()


@router.get("", response_model=list[UsuarioResponse])
async def listar_usuarios(
    limit: int = 50,
    offset: int = 0,
    grant: PermissionGrant = Depends(require_permission("usuarios:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: UsuarioService = Depends(_get_service),
):
    """Lista usuarios activos del tenant con PII descifrada."""
    users = await service.list(
        tenant_id=current_user.tenant_id,
        session=db,
        limit=limit,
        offset=offset,
    )

    result = []
    for user in users:
        pii = await service.decrypt_pii(user)
        result.append(
            UsuarioResponse(
                id=str(user.id),
                tenant_id=str(user.tenant_id),
                email=None,  # email se descifra por separado si se requiere
                nombre=user.nombre,
                apellidos=user.apellidos,
                legajo=user.legajo,
                legajo_profesional=user.legajo_profesional,
                banco=user.banco,
                regional=user.regional,
                facturador=user.facturador or False,
                is_active=user.is_active,
                dni=pii.get("dni"),
                cuil=pii.get("cuil"),
                cbu=pii.get("cbu"),
                alias_cbu=pii.get("alias_cbu"),
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
        )
    return result


@router.get("/{id}", response_model=UsuarioResponse)
async def obtener_usuario(
    id: uuid.UUID,
    grant: PermissionGrant = Depends(require_permission("usuarios:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: UsuarioService = Depends(_get_service),
):
    """Retorna un usuario por ID con PII descifrada."""
    try:
        user = await service.get(tenant_id=current_user.tenant_id, id=id, session=db)
    except UsuarioServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    pii = await service.decrypt_pii(user)
    return UsuarioResponse(
        id=str(user.id),
        tenant_id=str(user.tenant_id),
        email=None,
        nombre=user.nombre,
        apellidos=user.apellidos,
        legajo=user.legajo,
        legajo_profesional=user.legajo_profesional,
        banco=user.banco,
        regional=user.regional,
        facturador=user.facturador or False,
        is_active=user.is_active,
        dni=pii.get("dni"),
        cuil=pii.get("cuil"),
        cbu=pii.get("cbu"),
        alias_cbu=pii.get("alias_cbu"),
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.post("", response_model=UsuarioResponse, status_code=201)
async def crear_usuario(
    body: UsuarioCreate,
    grant: PermissionGrant = Depends(require_permission("usuarios:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: UsuarioService = Depends(_get_service),
):
    """Crea un usuario con PII cifrada. Devuelve PII descifrada en la response."""
    try:
        user = await service.create(
            tenant_id=current_user.tenant_id,
            actor_id=current_user.id,
            email=body.email,
            password_plain=body.password,
            nombre=body.nombre,
            apellidos=body.apellidos,
            legajo=body.legajo,
            legajo_profesional=body.legajo_profesional,
            banco=body.banco,
            regional=body.regional,
            facturador=body.facturador,
            dni=body.dni,
            cuil=body.cuil,
            cbu=body.cbu,
            alias_cbu=body.alias_cbu,
            session=db,
        )
    except UsuarioServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    pii = await service.decrypt_pii(user)
    return UsuarioResponse(
        id=str(user.id),
        tenant_id=str(user.tenant_id),
        email=body.email,  # En claro — solo en response de creación admin
        nombre=user.nombre,
        apellidos=user.apellidos,
        legajo=user.legajo,
        legajo_profesional=user.legajo_profesional,
        banco=user.banco,
        regional=user.regional,
        facturador=user.facturador or False,
        is_active=user.is_active,
        dni=pii.get("dni"),
        cuil=pii.get("cuil"),
        cbu=pii.get("cbu"),
        alias_cbu=pii.get("alias_cbu"),
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.put("/{id}", response_model=UsuarioResponse)
async def actualizar_usuario(
    id: uuid.UUID,
    body: UsuarioUpdate,
    grant: PermissionGrant = Depends(require_permission("usuarios:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: UsuarioService = Depends(_get_service),
):
    """Actualiza campos de un usuario. Solo se actualizan los campos provistos."""
    data = body.model_dump(exclude_none=True)
    try:
        user = await service.update(
            tenant_id=current_user.tenant_id,
            id=id,
            actor_id=current_user.id,
            data=data,
            session=db,
        )
    except UsuarioServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    pii = await service.decrypt_pii(user)
    return UsuarioResponse(
        id=str(user.id),
        tenant_id=str(user.tenant_id),
        email=None,
        nombre=user.nombre,
        apellidos=user.apellidos,
        legajo=user.legajo,
        legajo_profesional=user.legajo_profesional,
        banco=user.banco,
        regional=user.regional,
        facturador=user.facturador or False,
        is_active=user.is_active,
        dni=pii.get("dni"),
        cuil=pii.get("cuil"),
        cbu=pii.get("cbu"),
        alias_cbu=pii.get("alias_cbu"),
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.delete("/{id}", status_code=204)
async def eliminar_usuario(
    id: uuid.UUID,
    grant: PermissionGrant = Depends(require_permission("usuarios:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: UsuarioService = Depends(_get_service),
):
    """Soft delete de un usuario. El registro se conserva para auditoría."""
    try:
        await service.delete(
            tenant_id=current_user.tenant_id,
            id=id,
            actor_id=current_user.id,
            session=db,
        )
    except UsuarioServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
