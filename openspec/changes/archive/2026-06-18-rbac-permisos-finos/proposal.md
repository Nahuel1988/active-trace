## Why

C-03 dejó la autenticación lista (JWT + 2FA + recuperación) y los modelos `Role` / `UserRole` con vigencia, pero **no existe aún autorización**: ningún endpoint puede exigir un permiso, no hay catálogo de permisos ni matriz rol × permiso, y `app/core/permissions.py` quedó reservado vacío para este change. Sin C-04 no se puede proteger ninguna capacidad de negocio (calificaciones, comunicación, liquidaciones, auditoría), por lo que es bloqueante del camino crítico (`C-03 → C-04 → C-06 …`).

Este change implementa el modelo RBAC de permisos finos `modulo:accion` exigido por la regla dura #10 (fail-closed) y por `03_actores_y_roles.md §3` y `08_arquitectura_propuesta.md §3.2`: catálogo administrable como datos (no hardcode), resolución de permisos efectivos server-side por request, y el guard `require_permission(...)` que toda capa de transporte usará de aquí en adelante.

## What Changes

- **Nuevo modelo `Permiso`** (`modulo:accion`) como catálogo de capacidades atómicas, tenant-scoped y soft-delete.
- **Nueva matriz `RolPermiso`** (asociación rol ↔ permiso) como datos administrables, NO hardcodeada.
- **Migración Alembic 003** (`rol_permiso` + `permiso`; las tablas `role`/`user_role` ya existen desde 002) con el seed de la matriz base de `03_actores_y_roles.md §3.3` para los 7 roles del dominio (ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS).
- **Resolución de permisos efectivos server-side**: por request, unión de los permisos de todos los roles del usuario, acotada por `tenant_id` y por la **vigencia** de cada `UserRole` (`desde ≤ now < hasta|∞`). Los permisos NUNCA viajan en el JWT.
- **Dependency/guard `require_permission("modulo:accion")`** en `app/core/permissions.py`: declara el permiso exigido por endpoint. Fail-closed → sin permiso explícito devuelve **403**.
- **Semántica `(propio)` vs global**: el guard distingue permisos de alcance global de los de alcance propio; el guard concede el permiso y expone el alcance resuelto para que el Service valide ownership (la verificación de "sobre sus propios datos" es responsabilidad del Service, no del Router).
- **Endpoints de administración del catálogo** (CRUD de roles, permisos y asignación rol↔permiso) protegidos por `usuarios:gestionar`, para que la matriz sea administrable por tenant.
- **MODIFICADO** `auth-session`: el claim `roles` del access token pasa a derivarse de las asignaciones `UserRole` **vigentes** (antes podía no contemplar vigencia); se documenta explícitamente que los permisos se resuelven desde DB en cada request y nunca desde el token.

## Capabilities

### New Capabilities
- `rbac-permission-catalog`: catálogo administrable de permisos (`Permiso`, `modulo:accion`) y la matriz rol × permiso (`RolPermiso`), tenant-scoped, soft-delete, con seed inicial de la matriz de `03_actores_y_roles.md §3.3`.
- `rbac-effective-permissions`: resolución server-side, por request, de los permisos efectivos de un usuario como unión de sus roles vigentes, acotada por tenant y por la vigencia de las asignaciones.
- `rbac-require-permission`: dependency/guard `require_permission("modulo:accion")` fail-closed (403 sin permiso), con semántica de alcance `(propio)` vs global expuesta al Service.

### Modified Capabilities
- `auth-session`: el claim `roles` se deriva de las asignaciones `UserRole` vigentes; se reafirma que los permisos jamás se incluyen en el token y se resuelven server-side por request.

## Impact

- **Modelos**: nuevos `app/models/permiso.py` (`Permiso`, `RolPermiso`). `app/models/role.py` ya existe (C-03).
- **Repositories**: nuevos `permiso_repository.py`, `rol_permiso_repository.py`, `role_repository.py`, y resolución de permisos efectivos (query con join `UserRole`→`RolPermiso`→`Permiso` filtrada por tenant + vigencia).
- **Services**: `permission_service.py` (resolución de efectivos), `rbac_admin_service.py` (administración del catálogo).
- **Core**: `app/core/permissions.py` deja de estar reservado → implementa `require_permission` y `Scope` (`global`/`propio`).
- **Routers**: nuevo `routers/rbac.py` (administración de catálogo y matriz); `get_current_user` / dependencias de auth se extienden para exponer permisos efectivos.
- **Migración**: Alembic `003_rbac` (`permiso`, `rol_permiso`) + seed de la matriz base.
- **Auth**: ajuste en la emisión del claim `roles` (vigencia) — toca `token_service.py` / `auth_service.py`.
- **Dominio CRÍTICO** (governance): cambios solo tras aprobación humana; sin impacto en tablas de auth existentes salvo el cálculo del claim `roles`.
