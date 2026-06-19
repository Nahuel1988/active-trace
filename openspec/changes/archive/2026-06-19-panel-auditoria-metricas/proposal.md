## Why

C-05 dejó la tabla `audit_log` poblándose con cada acción significativa del sistema (append-only, multi-tenant, atribución bajo impersonación), pero **no existe ninguna vía de lectura supervisada** de esos datos. COORDINADOR, ADMIN y FINANZAS no pueden hoy responder preguntas operativas básicas: ¿quién importó qué y cuándo?, ¿qué docentes están inactivos?, ¿qué comunicaciones fallaron?. C-19 cierra la Épica 9 (Auditoría y Métricas de Uso) entregando el panel de supervisión (F9.1) y el log completo filtrable (F9.2) descritos en FL-11, **solo lectura** sobre la tabla que C-05 ya escribe.

## What Changes

- **Panel de interacciones (F9.1)** — endpoints de agregación de solo lectura sobre `audit_log`:
  - Acciones por día (serie temporal de volumen de uso).
  - Estado de comunicaciones agrupado por docente (Pendiente / Enviando / Enviado / Fallido / Cancelado).
  - Interacciones por docente × materia (conteo por código de acción).
  - Log de últimas acciones (límite configurable por el cliente, **defecto 200**, tope máximo de seguridad).
- **Log completo de auditoría (F9.2, RN-23/24)** — endpoint de listado paginado con filtros: rango de fechas, materia, usuario, estado/código de acción.
- **Filtros comunes** a todas las vistas: rango de fechas, materia, usuario, estado de actividad.
- **Guard RBAC `auditoria:ver`** en `/api/v1/auditoria/*`, **fail-closed**.
- **Scope diferenciado por rol** (matriz §3.3 de `03_actores_y_roles.md`):
  - **ADMIN**: lectura global de todo el tenant.
  - **COORDINADOR**: lectura acotada a su propio scope `(propio)` — solo las acciones que él mismo ejecutó.
  - **FINANZAS**: lectura (alcance del tenant, igual que ADMIN para auditoría según la matriz).
- **Sin escritura**: este change NO inserta, modifica ni elimina registros de `audit_log`. Reutiliza el `AuditLogRepository` de C-05 (append-only) extendiéndolo solo con métodos de lectura/agregación. No hay migración Alembic nueva (índice `ix_audit_log_tenant_fecha` ya existe).

## Capabilities

### New Capabilities
- `audit-panel`: Panel de métricas e interacciones de uso (F9.1) — agregaciones de solo lectura sobre `audit_log`: acciones por día, estado de comunicaciones por docente, interacciones por docente×materia, y log de últimas acciones con límite configurable.
- `audit-query`: Log completo de auditoría filtrable (F9.2, RN-23/24) — listado paginado de registros de `audit_log` con filtros de fecha, materia, usuario y código de acción, y aplicación del scope por rol (global vs. `(propio)` del coordinador).

### Modified Capabilities
<!-- Ninguna. C-19 NO modifica los requisitos de `audit-log` ni `auth-impersonation` (C-05): consume la tabla append-only existente en modo solo lectura. Los métodos de lectura/agregación que se agregan al AuditLogRepository no alteran su contrato de inmutabilidad (siguen sin existir update/delete). -->

## Impact

- **Código nuevo**:
  - `backend/app/api/v1/routers/auditoria.py` — router `/api/v1/auditoria/*` con guard `auditoria:ver`.
  - `backend/app/services/auditoria_service.py` — orquesta agregaciones y aplica el scope por rol (identidad/roles desde la sesión).
  - `backend/app/schemas/auditoria.py` — DTOs Pydantic v2 (`extra='forbid'`): filtros de query y respuestas de cada vista.
- **Código extendido**:
  - `backend/app/repositories/audit_log_repository.py` — nuevos métodos de **solo lectura**: `aggregate_acciones_por_dia`, `aggregate_comunicaciones_por_docente`, `aggregate_interacciones_docente_materia`, y un `list` enriquecido con filtros y scope. NO se agregan métodos de mutación.
- **Permiso**: `auditoria:ver` debe existir en el catálogo RBAC (C-04) y estar asignado a ADMIN, COORDINADOR y FINANZAS.
- **Dependencias**: C-05 `audit-log` (archivado ✅, provee modelo `AuditLog` + repo append-only) y C-07 (en progreso — provee la entidad `Materia` para resolver `materia_id` en filtros y agregaciones).
- **Sin impacto en escritura ni migraciones**: no se toca la inmutabilidad de `audit_log` ni se crea schema nuevo.
- **Governance: ALTO** — dominio de auditoría. Este change es solo lectura, pero un fallo de scope (un coordinador viendo acciones ajenas, o fuga cross-tenant) es un defecto de seguridad. Todo query parte del `tenant_id` de la sesión y el scope se deriva de los roles de la sesión, nunca de la petición.
