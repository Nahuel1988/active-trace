## Context

C-05 (`audit-log`, archivado) entregó la tabla `audit_log` como registro **append-only** e inmutable (reglas PostgreSQL `ON UPDATE/DELETE DO INSTEAD NOTHING`, migración 004), su modelo `backend/app/models/audit_log.py`, el `AuditLogRepository` (solo `add` + `list` tenant-scoped, sin `update`/`delete`), el helper `audit_action`, el decorator `@audited` y el catálogo `AuditCodes`. Cada acción significativa del sistema ya inserta una fila con: `tenant_id`, `fecha_hora`, `actor_id`, `impersonado_id`, `materia_id` (nullable), `accion`, `detalle` (JSONB), `filas_afectadas`, `ip`, `user_agent`. Existe el índice compuesto `ix_audit_log_tenant_fecha (tenant_id, fecha_hora)`.

C-19 construye **solo la capa de lectura** sobre esa tabla: el panel de interacciones (F9.1) y el log filtrable (F9.2), siguiendo FL-11. No hay ingesta ni mutación nueva. La arquitectura sigue Clean (Routers → Services → Repositories → Models), identidad siempre desde JWT, multi-tenancy row-level, RBAC fail-closed.

**Restricciones duras vigentes**: identidad/roles/tenant solo desde la sesión; repositories filtran por tenant por defecto; sin lógica de negocio en routers; sin acceso a DB desde services salvo vía repository; Pydantic `extra='forbid'`; snake_case; ≤500 LOC por archivo; TDD estricto (≥80% líneas, ≥90% reglas de negocio); tests con DB real/efímera, sin mockear la base.

**Governance: ALTO** (dominio auditoría). Solo lectura, pero un error de scope (coordinador viendo acciones ajenas) o una fuga cross-tenant son defectos de seguridad. El scope se decide en el service a partir de los roles de la sesión, y el repository siempre parte del `tenant_id`.

## Goals / Non-Goals

**Goals:**
- Endpoints `/api/v1/auditoria/*` de **solo lectura** con guard `auditoria:ver` fail-closed.
- Panel F9.1: acciones por día, estado de comunicaciones por docente, interacciones por docente×materia, log de últimas acciones (límite configurable, defecto 200, con tope de seguridad).
- Log F9.2: listado paginado con filtros (rango de fechas, materia, usuario, código de acción).
- Scope diferenciado: ADMIN/FINANZAS global del tenant; COORDINADOR solo su propio `actor_id` (`(propio)`), nunca ampliable por la petición.
- Reutilizar `AuditLogRepository` extendiéndolo **solo** con métodos de lectura/agregación, preservando su contrato append-only (sigue sin `update`/`delete`).

**Non-Goals:**
- NO se escribe, modifica ni elimina nada en `audit_log` (la inmutabilidad de C-05 queda intacta).
- NO se crea migración Alembic (el índice ya existe; se evalúa solo si las agregaciones lo exigen — ver Open Questions).
- NO se implementa el frontend del panel (eso es C-24, consume estos endpoints).
- NO se modifican los requisitos de los specs de C-05 (`audit-log`, `auth-impersonation`).
- NO se resuelve el filtro "estado de actividad activo/inactivo" del usuario más allá de lo que `audit_log` permite (ver Open Questions / decisión D5).

## Decisions

### D1 — Scope por rol resuelto en el Service, aplicado en el Repository
El `AuditoriaService` recibe el `current_user` (de la sesión) y calcula un `scope_actor_id`: `None` si el usuario tiene rol ADMIN o FINANZAS (lectura global del tenant), o `current_user.id` si su rol efectivo de auditoría es solo COORDINADOR. Ese `scope_actor_id` se pasa como parámetro a cada método del repository, que lo combina con el `tenant_id` obligatorio en el `WHERE`. **Por qué**: la decisión de scope es lógica de negocio (depende de roles) → vive en el service; el filtrado SQL vive en el repository. El router solo declara el guard y delega.
**Alternativa descartada**: filtrar en el router con dependencias RBAC — mezclaría lógica de negocio en la capa de presentación (viola regla dura 11).

### D2 — Extender AuditLogRepository, no crear uno nuevo
Se agregan al `AuditLogRepository` existente métodos de **solo lectura**: `aggregate_acciones_por_dia`, `aggregate_comunicaciones_por_docente`, `aggregate_interacciones_docente_materia`, y un `list_filtrado` (o se enriquece `list`) con parámetros opcionales `scope_actor_id`, `desde`, `hasta`, `materia_id`, `accion`, `limit`, `offset`. **No** se agrega ningún método de mutación: `create`/`update`/`soft_delete` siguen lanzando `NotImplementedError`. **Por qué**: mantiene una única puerta de acceso a `audit_log` y preserva el contrato append-only verificable. Si el archivo se acerca a 500 LOC, separar las agregaciones en un `AuditLogQueryRepository` de solo lectura que comparta el modelo.
**Alternativa descartada**: queries crudas en el service — viola la regla "sin DB en services".

### D2b — Agregaciones en SQL, no en Python
Las agregaciones (`COUNT`, `GROUP BY` por `date_trunc('day', fecha_hora)`, por `actor_id`, por `(actor_id, materia_id, accion)`) se resuelven en PostgreSQL vía SQLAlchemy, no cargando filas a memoria. **Por qué**: `audit_log` crece sin límite (append-only); agregar en Python no escala y multiplica el costo. El índice `(tenant_id, fecha_hora)` cubre el filtro base y la serie por día.

### D3 — Estado de comunicaciones derivado de los códigos de acción
F9.1 pide "estado de comunicaciones (Pendiente/Enviando/Enviado/Fallido/Cancelado) por docente". El estado se deriva de los códigos de acción de comunicación registrados en `audit_log` (`COMUNICACION_ENVIAR` y los que C-12 agregue al catálogo), o del campo `detalle` JSONB si el estado vive ahí. **Por qué**: este change es solo lectura sobre `audit_log`; no consulta la tabla de comunicaciones de C-12 para no acoplar dominios. El mapeo exacto código→estado se fija contra el catálogo `AuditCodes` disponible al implementar (ver Open Questions Q2).

### D4 — Límite configurable con tope de seguridad
El log de últimas acciones (F9.1) y el log completo (F9.2) aceptan `limit` desde el query. Defecto **200** (F9.1) y un defecto razonable paginado para F9.2. Se aplica un **tope máximo** (constante, p. ej. `AUDIT_LOG_MAX_LIMIT = 1000`): si el cliente pide más, se recorta al tope. Validación vía Pydantic v2 (`Field(default=200, ge=1, le=MAX)`) en el DTO de query, con `extra='forbid'`. **Por qué**: evita que una petición arrastre toda la tabla a memoria (DoS accidental). El recorte es silencioso (no error) según los specs.

### D5 — Filtro "estado de actividad" del usuario fuera del alcance de audit_log
FL-11 menciona filtrar por "estado de actividad (activo/inactivo)" del docente. `audit_log` no almacena el estado del usuario; ese dato vive en `User` (C-02). Para no acoplar, C-19 interpreta "estado" primariamente como **estado/código de acción** (filtro implementado, D-spec). Si se requiere el activo/inactivo del usuario, se resuelve en el service cruzando con `UserRepository` por `tenant_id` — se deja como tarea opcional marcada, no bloqueante. **Por qué**: mantener el core del change como solo-lectura sobre `audit_log` y no expandir scope.

### D6 — DTOs Pydantic v2 con extra='forbid'
`backend/app/schemas/auditoria.py` define: `AuditoriaFiltros` (query: desde, hasta, materia_id, actor_id, accion, limit, offset), y respuestas (`AccionesPorDiaResponse`, `ComunicacionesPorDocenteResponse`, `InteraccionesResponse`, `LogAccionItem`/`LogResponse`). Todos con `model_config = ConfigDict(extra='forbid')`. El `actor_id` del filtro nunca decide identidad: solo acota dentro del scope ya calculado.

## Risks / Trade-offs

- **[Fuga de scope: COORDINADOR ve acciones ajenas]** → El `scope_actor_id` se calcula SOLO desde los roles de la sesión; el `actor_id` del query nunca puede ampliarlo (test dedicado: coordinador filtrando por otro actor obtiene 0 registros). Cubierto por specs `audit-panel` y `audit-query`.
- **[Fuga cross-tenant]** → El `tenant_id` de la sesión es obligatorio en TODO método del repository; test de aislamiento entre tenants (datos de A invisibles para B). Hereda la garantía probada en C-05.
- **[Performance de agregaciones sobre tabla creciente]** → Agregación en SQL + índice `(tenant_id, fecha_hora)`. Riesgo residual en `GROUP BY (actor_id, materia_id, accion)` sin índice dedicado; si surge en pruebas de volumen, evaluar índice adicional (Open Question Q1).
- **[Acoplamiento accidental a C-12/C-07]** → C-07 (Materia) está en progreso: `materia_id` se filtra por valor crudo (UUID) sin join obligatorio; la resolución de nombre de materia es opcional/diferible. El estado de comunicaciones se deriva de `audit_log`, no de la tabla de C-12. Reduce el acoplamiento a dependencia de datos, no de código.
- **[Romper la inmutabilidad de C-05]** → Solo se agregan métodos de lectura; `create/update/soft_delete` siguen lanzando `NotImplementedError`. Un test verifica que el repo extendido no expone mutación.

## Migration Plan

- **Sin migración de schema** prevista: `audit_log` y su índice ya existen (C-05). El permiso `auditoria:ver` debe existir en el catálogo RBAC (C-04) y estar asignado a ADMIN, COORDINADOR y FINANZAS; si falta el seed, agregarlo como tarea de datos (no migración estructural).
- **Despliegue**: feature puramente aditiva (nuevos endpoints de solo lectura). Sin cambios destructivos.
- **Rollback**: quitar el router del `api/v1` y los archivos nuevos; no hay estado persistido que revertir.

## Open Questions

- **Q1**: ¿Hace falta un índice adicional para `GROUP BY (actor_id, materia_id, accion)`? Decidir tras prueba de volumen; no bloquea la implementación funcional. Si se necesita, será **una** migración Alembic dedicada.
- **Q2**: ¿El estado de comunicaciones (Pend/Enviando/OK/Fallido/Cancelado) está como códigos de acción distintos en `AuditCodes` o como campo dentro de `detalle` JSONB? Confirmar contra el catálogo vigente al implementar (C-12 puede haberlo extendido). Define el mapeo de D3.
- **Q3**: ¿FINANZAS lee auditoría global del tenant igual que ADMIN, o con algún recorte? La matriz §3.3 marca `Ver auditoría: FINANZAS ✅` (sin `(propio)`), por lo que se asume global. Confirmar con el usuario si debe acotarse a dominio financiero.
