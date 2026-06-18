## 1. Modelos y schema (rbac-permission-catalog)

- [ ] 1.1 Crear `app/models/permiso.py` con el modelo `Permiso` (TenantScopedMixin: `modulo`, `accion`, `code` derivado, soft-delete) y `UNIQUE(tenant_id, code)` + índice tenant/deleted
- [ ] 1.2 Añadir el modelo de asociación `RolPermiso` (PK compuesta `(tenant_id, role_id, permiso_id)`, columna `scope` con CHECK/Enum {`global`,`propio`}, FKs a `role`/`permiso`/`tenant`) en `app/models/permiso.py`
- [ ] 1.3 Registrar `Permiso` y `RolPermiso` en `app/models/__init__.py`
- [ ] 1.4 Definir el set de permisos del dominio y la matriz base como estructura de datos en un módulo seed (`app/core/rbac_seed.py`) derivada 1:1 de `03_actores_y_roles.md §3.3` (incluye scopes `propio`/`global`; NEXO solo transversales — confirmar PA-25)

## 2. Migración 003 (rbac-permission-catalog)

- [ ] 2.1 Generar `alembic/versions/003_rbac.py`: `create_table permiso` + `create_table rol_permiso` con PK compuesta, FKs e índices tenant-scoped
- [ ] 2.2 Añadir data migration idempotente en la 003: insertar catálogo de permisos + filas de la matriz base por cada tenant existente (check-then-insert / ON CONFLICT DO NOTHING)
- [ ] 2.3 Implementar `downgrade` que borre `rol_permiso` y `permiso`
- [ ] 2.4 (TDD) Test de migración: aplicar upgrade sobre DB de test (sin mocks) y verificar tablas, constraints y que el seed deja las filas esperadas de la matriz (celda ✅ → global, `(propio)` → propio, — → sin fila); test de idempotencia (doble run)

## 3. Repositories (rbac-permission-catalog + effective-permissions)

- [ ] 3.1 (TDD) Test de `RoleRepository` (tenant-scoped) → implementar `app/repositories/role_repository.py`
- [ ] 3.2 (TDD) Test de `PermisoRepository` (CRUD tenant-scoped, soft-delete, unicidad de code) → implementar `app/repositories/permiso_repository.py`
- [ ] 3.3 (TDD) Test de `RolPermisoRepository` (asignar/quitar permiso a rol, listar matriz por tenant) → implementar `app/repositories/rol_permiso_repository.py`
- [ ] 3.4 (TDD) Test del query de permisos efectivos (join `UserRole`→`RolPermiso`→`Permiso` con filtro tenant + vigencia + soft-delete) → implementar el método en el repositorio correspondiente

## 4. Resolución de permisos efectivos (rbac-effective-permissions)

- [ ] 4.1 (TDD) Test `PermissionService.get_effective_permissions`: unión de roles, acotado por tenant — happy path + edge → implementar `app/services/permission_service.py`
- [ ] 4.2 (TDD) Test de vigencia: asignación vigente otorga, vencida no otorga (y persiste en histórico), futura no otorga
- [ ] 4.3 (TDD) Test de resolución de scope en conflicto: global gana sobre propio; solo-propio cuando ningún rol lo da global
- [ ] 4.4 (TDD) Test: usuario sin roles vigentes → conjunto vacío
- [ ] 4.5 (TDD) Test: los permisos se resuelven desde DB y un claim `roles` manipulado en el token no agrega permisos

## 5. Guard require_permission (rbac-require-permission)

- [ ] 5.1 Reemplazar el stub de `app/core/permissions.py`: definir `Scope` ({`global`,`propio`}) y `PermissionGrant(code, scope)`
- [ ] 5.2 (TDD) Test del guard: con permiso presente concede y entrega `PermissionGrant`; sin permiso → 403 (fail-closed) → implementar `require_permission(code)` como dependency factory
- [ ] 5.3 (TDD) Test: usuario sin roles vigentes → 403; petición sin token válido → 401 (antes de evaluar autorización)
- [ ] 5.4 (TDD) Test de `is_allowed(grant, owner_id, current_user_id)`: global concede siempre; propio concede solo sobre recurso propio; propio deniega recurso ajeno → implementar la utilidad
- [ ] 5.5 (TDD) Test: la identidad usada por el guard viene del JWT, ignorando parámetros de la petición

## 6. Ajuste de claims roles vigentes (auth-session MODIFIED)

- [ ] 6.1 (TDD) Test: el claim `roles` del access token incluye solo asignaciones `UserRole` vigentes y omite vencidas → ajustar emisión en `token_service.py` / `auth_service.py`
- [ ] 6.2 (TDD) Test: el token no contiene permisos; `get_current_user` no usa el claim `roles` como fuente de autorización

## 7. Administración del catálogo y la matriz (rbac-permission-catalog)

- [ ] 7.1 Crear schemas Pydantic (`extra='forbid'`) para crear/listar permisos, roles y asignaciones de matriz en `app/schemas/rbac.py`
- [ ] 7.2 (TDD) Test de `RbacAdminService` (crear permiso, asignar/quitar permiso a rol, listar matriz, acotado por tenant) → implementar `app/services/rbac_admin_service.py`
- [ ] 7.3 Crear `app/api/v1/routers/rbac.py` con endpoints de administración, cada uno con `require_permission("usuarios:gestionar")`
- [ ] 7.4 Registrar el router en `app/api/v1/routers/__init__.py`
- [ ] 7.5 (TDD) Tests de endpoint: con `usuarios:gestionar` → 200; sin permiso → 403; cross-tenant → 404; body con campo extra → 422

## 8. Cierre

- [ ] 8.1 Verificar cobertura ≥80% líneas / ≥90% reglas de negocio del módulo RBAC
- [ ] 8.2 Verificar que ningún archivo backend supera 500 LOC; refactorizar si hace falta
- [ ] 8.3 Confirmar PA-25 (permisos exactos de NEXO) con el usuario y ajustar el seed si corresponde
