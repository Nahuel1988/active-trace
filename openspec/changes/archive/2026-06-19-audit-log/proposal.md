## Why

El sistema necesita trazabilidad completa de todas las acciones significativas desde el momento en que los primeros módulos de negocio (estructura académica, padrón, comunicaciones) comiencen a operar. Sin el audit log en su lugar, cualquier acción realizada antes de C-19 (panel de auditoría) quedará sin registro y la promesa del producto — *todo audita* — se romperá retroactivamente.

## What Changes

- **Nuevo modelo `AuditLog` (E-AUD)** append-only: campos `actor_id`, `impersonado_id`, `materia_id`, `accion`, `detalle` (JSON), `filas_afectadas`, `ip`, `user_agent`, `fecha_hora`, `tenant_id`. Sin update ni delete a nivel de aplicación ni de base de datos.
- **Migración 003** (`003_audit_log`): crea la tabla `audit_log` con constraint DB-level que impide UPDATE/DELETE mediante regla PostgreSQL.
- **`AuditLogRepository`**: solo operaciones `add` y `list`; queries de lectura con scope de tenant; sin métodos de mutación expuestos.
- **Helper `audit_action`**: función async que registra una entrada en el log desde cualquier service. Acepta el contexto de request (actor, ip, user_agent) y el código de acción estandarizado.
- **Decorator `@audited`**: decorador para routers/services que llama a `audit_action` automáticamente al completar una operación (code de acción + filas afectadas).
- **Impersonación**: endpoint `/api/auth/impersonate/{user_id}` (POST/DELETE) que requiere `impersonacion:usar`; genera un JWT distinguible (`"impersonated": true`, `actor_id` real); registra `IMPERSONACION_INICIAR` y `IMPERSONACION_FINALIZAR` en el audit log.

## Capabilities

### New Capabilities

- `audit-log`: Modelo AuditLog append-only, repositorio de solo escritura/lectura, helper `audit_action` y decorator `@audited` con catálogo de códigos de acción.
- `auth-impersonation`: Inicio y fin de sesión de impersonación permisada; JWT distinguible con `actor_id` real; atribución de acciones al actor real en el log.

### Modified Capabilities

- `auth-session`: El payload del JWT incorpora el flag `impersonated` y `actor_id` para que `get_current_user` lo exponga al stack de permisos.

## Impact

- **Backend**: nuevo modelo `AuditLog`, repositorio, helper y decorator en `backend/app/core/`; migración Alembic 003; extensión del payload JWT (`actor_id`, `impersonated`).
- **RBAC seed**: permiso `impersonacion:usar` ya incluido en seed de C-04; no requiere cambio de seed.
- **Dependencia transitiva**: todos los changes futuros que registren acciones (C-08, C-09, C-10, C-12…) importarán `audit_action` / `@audited` de este módulo.
- **Sin cambio de API pública** para los consumidores existentes (auth endpoints de C-03); solo el JWT se extiende con campos opcionales.
