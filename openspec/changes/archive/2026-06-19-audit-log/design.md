## Context

C-04 (RBAC) está completo: todos los endpoints declaran `require_permission` y el sistema tiene identidad verificada. El siguiente paso según el camino crítico es C-05: establecer el audit log append-only antes de que los módulos de negocio (C-06+) empiecen a generar acciones auditables. El modelo `AuditLog` (E-AUD) está definido en la KB; este design concreta las decisiones de implementación.

Estado actual: no existe tabla `audit_log`, no existe helper de auditoría, ni endpoint de impersonación.

## Goals / Non-Goals

**Goals:**
- Modelo `AuditLog` con garantía DB-level de inmutabilidad (ningún UPDATE/DELETE posible).
- `AuditLogRepository` con métodos exclusivos: `add` (escritura) y `list` (lectura tenant-scoped).
- Helper `audit_action(...)` async inyectable desde cualquier service.
- Decorator `@audited(accion, ...)` para routers que automatiza el registro.
- Impersonación: endpoint `/api/auth/impersonate/{user_id}` (POST/DELETE), JWT distinguible, atribución al actor real.
- Catálogo de códigos de acción como `Enum` o constantes tipadas en `backend/app/core/audit_codes.py`.

**Non-Goals:**
- Panel de visualización del log (C-19).
- Exportación de logs (C-19).
- Retención configurable o purga automática (fuera de scope del producto actual).
- Auditoría de lecturas (solo acciones significativas de escritura/modificación).

## Decisions

### D-01: Inmutabilidad enforced en la DB con regla PostgreSQL

**Decisión**: crear una regla `ON UPDATE DO INSTEAD NOTHING` y `ON DELETE DO INSTEAD NOTHING` en la tabla `audit_log` via Alembic (SQL raw en la migración 003). No solo a nivel ORM.

**Alternativas consideradas**:
- Solo prohibir update/delete en el ORM (Repository sin métodos de mutación): insuficiente — acceso directo a DB o futuros cambios en el ORM podrían bypassearlo.
- Row-Level Security de PostgreSQL: más potente pero requiere configuración de roles de DB que no tenemos en scope.

**Rationale**: La garantía debe vivir en la base de datos, no solo en la capa de aplicación. Un `CREATE RULE` es simple, declarativo y no requiere privilegios de superuser.

```sql
CREATE RULE audit_log_no_update AS ON UPDATE TO audit_log DO INSTEAD NOTHING;
CREATE RULE audit_log_no_delete AS ON DELETE TO audit_log DO INSTEAD NOTHING;
```

### D-02: `audit_action` como función async, no solo como decorator

**Decisión**: exponer `audit_action(ctx, accion, detalle, filas_afectadas, materia_id)` como función async standalone, y además `@audited(accion)` como thin wrapper decorator sobre ella.

**Alternativas consideradas**:
- Solo decorator: no sirve cuando la lógica de auditoría está en un service (fuera de la firma del router).
- Solo función: más verboso para el caso común de un router que siempre audita.

**Rationale**: La mayoría de los módulos futuros necesitarán auditar desde services (C-09, C-10, C-12), no desde el router. La función standalone es el primitivo; el decorator es azúcar para el caso simple.

### D-03: Contexto de auditoría en `AuditContext` dataclass

**Decisión**: definir `AuditContext(actor_id, tenant_id, ip, user_agent, impersonado_id?)` como dataclass extraída de `get_current_user`. El helper `audit_action` lo recibe como primer argumento.

**Rationale**: Evita pasar 5 parámetros sueltos en cada llamada. `get_current_user` ya tiene toda la información necesaria; la expone en un objeto tipado.

### D-04: JWT de impersonación con claims adicionales

**Decisión**: el token de impersonación es un access token normal con dos claims extra:
- `"impersonated": true` — distingue visualmente la sesión.
- `"actor_id": <UUID del admin real>` — quien realmente opera.

`get_current_user` lee estos claims y los expone en el `CurrentUser` context object. El `sub` del token es el `user_id` del usuario impersonado (para que los permisos del impersonado se carguen correctamente); el `actor_id` es quien audita.

**Alternativas consideradas**:
- Nuevo tipo de token (`type=impersonation`): más limpio semánticamente pero rompe la dependency `get_current_user` existente que valida `type=access`.
- Header extra `X-Impersonated-As`: más flexible pero no viaja en el JWT y requiere validación separada.

**Rationale**: Extender el access token es la mínima intervención: las guards de permisos siguen funcionando con los roles del impersonado (soporte ve lo que el usuario ve), y el `actor_id` permite que `AuditContext` atribuya la acción al admin real.

### D-05: Migración 003 con `execute(text(...))` para las reglas

**Decisión**: la migración Alembic 003 crea la tabla con SQLAlchemy Core y luego ejecuta las reglas PostgreSQL con `op.execute(sa.text("CREATE RULE ..."))`. El `downgrade` elimina las reglas y la tabla.

**Rationale**: Alembic no tiene soporte nativo para `CREATE RULE`; SQL raw via `op.execute` es el mecanismo estándar para DDL no soportado.

## Risks / Trade-offs

- **[Riesgo] Las reglas PostgreSQL son silenciosas**: un `UPDATE` contra `audit_log` no lanza error, simplemente no hace nada (comportamiento de `INSTEAD NOTHING`). → Mitigación: test explícito que verifica que el registro no cambió tras un intento de update; log de warning si el ORM intenta una mutación.
- **[Trade-off] `actor_id` en el JWT aumenta el tamaño del token**: mínimo (un UUID extra, ~36 chars). Aceptable dado que solo ocurre en sesiones de impersonación (baja frecuencia).
- **[Riesgo] Volumen del log en producción**: sin retención configurable, la tabla crece indefinidamente. → Mitigación: índice en `(tenant_id, fecha_hora)` para queries eficientes; purga es trabajo de C-19/ops.

## Migration Plan

1. Aplicar migración 003: `alembic upgrade head` crea `audit_log` + reglas inmutabilidad.
2. No hay datos existentes que migrar (tabla nueva).
3. Rollback: `alembic downgrade -1` elimina reglas y tabla (sin pérdida de datos en otros módulos).

## Open Questions

- ¿El endpoint `DELETE /api/auth/impersonate` invalida el token de impersonación activo en el cliente, o solo registra el evento `IMPERSONACION_FINALIZAR`? → Decisión: solo registra el evento; la invalidación real es por expiración del JWT (15 min, igual que un token normal).
