## Context

C-07 ya entregó el modelo `Asignacion` (`backend/app/models/asignacion.py`), su `AsignacionRepository`, `AsignacionService` (con validación rol×contexto, detección de ciclos, soft-delete) y el CRUD individual en `app/api/v1/routers/asignaciones.py`. C-05 entregó el `AuditLogRepository` con el catálogo de acciones (`ASIGNACION_CREAR`, `ASIGNACION_MODIFICAR`, `ASIGNACION_BAJA`). C-04 entregó `require_permission("equipos:asignar")` y C-03 `get_current_user`.

**Coexistencia UserRole / Asignacion (C-07)**: ADMIN/FINANZAS se modelan en `UserRole`; PROFESOR/TUTOR/COORDINADOR/NEXO en `Asignacion`. El resolver de permisos hace UNION. **C-08 opera EXCLUSIVAMENTE sobre `Asignacion`** — no toca `UserRole`.

La pieza que falta es la capa de **operaciones a nivel "equipo"**. En el dominio, un *equipo* es el conjunto de asignaciones que comparten la tupla `(materia_id, carrera_id, cohorte_id)`. C-08 introduce esa noción como concepto operativo (no como tabla nueva): es una *vista derivada* de `Asignacion`.

## Goals / Non-Goals

**Goals:**
- Vista "mis equipos" del docente resuelta por identidad de sesión (F4.2).
- Operaciones de bloque atómicas sobre `Asignacion`: masiva (F4.4), clonado (F4.5/RN-12), vigencia en bloque (F4.6).
- Export CSV del equipo (F4.7).
- Toda operación de bloque audita con `filas_afectadas` real y emite `ASIGNACION_MODIFICAR` / `ASIGNACION_CREAR` según corresponda.
- Reutilizar al 100% las validaciones de `AsignacionService` (rol×contexto, desde≤hasta, ciclos, auto-supervisión).

**Non-Goals:**
- NO se crea una tabla `equipo` ni un modelo `Equipo`. El equipo es la tupla `(materia, carrera, cohorte)` sobre `Asignacion`.
- NO se modifica el contrato del modelo `Asignacion` ni el CRUD individual de C-07.
- NO se toca `UserRole` ni el resolver de permisos efectivos.
- NO export a XLSX/PDF en este change — CSV es el MVP (F4.7 pide "archivo descargable").
- NO UI; este change es backend. El frontend del equipo docente vive en el change frontend correspondiente.

## Decisions

### D1 — "Equipo" = tupla `(materia_id, carrera_id, cohorte_id)`, no entidad nueva
El equipo se identifica por la combinación de contexto académico. Las operaciones de bloque reciben esa tupla y operan sobre todas las `Asignacion` no soft-deleted que la comparten dentro del tenant.
- **Alternativa descartada**: crear tabla `equipo` con FK desde `asignacion`. Rechazada: agrega migración, redundancia y un punto de inconsistencia; el dominio (RN-12) ya define equipo como esa tupla.

### D2 — Router nuevo `/api/v1/equipos/*`, no extender el de asignaciones
Las operaciones de equipo viven en `app/api/v1/routers/equipos.py` con un `EquipoService` dedicado (`app/services/equipo_service.py`). El CRUD individual de C-07 queda en `/api/v1/asignaciones`.
- **Rationale**: separación de responsabilidades; el router de asignaciones es CRUD de fila, el de equipos es operación de agregado. Mantiene cada archivo <500 LOC (regla dura).
- Endpoints:
  - `GET  /api/v1/equipos/mis-equipos` — F4.2, SIN guard `equipos:asignar` (identidad de sesión).
  - `GET  /api/v1/equipos` — F4.3, lista equipos (tuplas distintas) con conteo; guard `equipos:asignar`.
  - `POST /api/v1/equipos/asignacion-masiva` — F4.4; guard `equipos:asignar`.
  - `POST /api/v1/equipos/clonar` — F4.5; guard `equipos:asignar`.
  - `PATCH /api/v1/equipos/vigencia` — F4.6; guard `equipos:asignar`.
  - `GET  /api/v1/equipos/export` — F4.7; guard `equipos:asignar`.

### D3 — "Mis equipos" se resuelve por `current_user.id`, nunca por parámetro
Regla dura #8: identidad siempre del JWT. `GET /mis-equipos` NO acepta `usuario_id` por query — usa `current_user.id`. Devuelve las asignaciones vigentes del usuario agrupadas por tupla de equipo. Por eso NO requiere `equipos:asignar` (ver el propio equipo es un derecho del docente, no una capacidad de coordinación). Filtra por `tenant_id` del JWT.

### D4 — Atomicidad: una sola transacción por operación de bloque
Las operaciones masiva/clonado/vigencia se ejecutan dentro de la sesión del request (un solo `commit` del lado del router/dependency). Si una fila falla validación en masiva, se decide por **política de bloque** (ver D5). El clonado y la vigencia en bloque son todo-o-nada: si cualquier paso lanza error, la transacción se revierte completa.

### D5 — Asignación masiva: validación por fila, reporte por bloque (best-effort con resumen)
Para cada `usuario_id` del bloque se invoca la validación de `AsignacionService` (rol×contexto, etc.). Las filas válidas se crean; las inválidas se reportan con motivo. La response devuelve `{creadas: N, rechazadas: [{usuario_id, motivo}]}`.
- **Decisión**: best-effort (crear las válidas) en vez de todo-o-nada, porque RN-30 (asignación masiva con autocompletado) implica que el coordinador arma un lote heterogéneo y espera ver qué entró y qué no. La transacción solo se revierte ante error de infraestructura, no ante rechazo de validación de una fila.
- **Idempotencia**: si un `(usuario, rol, materia, carrera, cohorte)` ya existe vigente, NO se duplica — se cuenta como "omitida (ya existe)".

### D6 — Clonado (RN-12): qué se copia, qué cambia, qué pasa con solapamientos
Origen = `(materia_id, carrera_id, cohorte_id)` origen. Destino = `(carrera_id, cohorte_id)` destino + nueva vigencia `desde`/`hasta`. La materia se mantiene (un equipo es de una materia) salvo que se pase `materia_id` destino explícito.
- **Se copia por cada asignación vigente del origen**: `usuario_id`, `role_id`, `comisiones`, `responsable_id`.
- **Se reescribe**: `carrera_id` y `cohorte_id` → destino; `desde`/`hasta` → nueva vigencia del período destino.
- **Solapamiento / idempotencia**: si en el destino ya existe una asignación vigente para `(usuario, rol, materia, carrera, cohorte)`, NO se duplica (se omite y se reporta). Esto hace el clonado **re-ejecutable** sin generar duplicados.
- **Solo asignaciones vigentes** del origen se clonan (RN-12 dice "todas las asignaciones de un equipo"; se interpreta como las vigentes, no el histórico vencido/soft-deleted).
- Response: `{clonadas: N, omitidas: [{usuario_id, motivo}]}`.

### D7 — Vigencia en bloque (F4.6): UPDATE masivo con validación desde≤hasta
`PATCH /vigencia` recibe la tupla de equipo + nuevas `desde`/`hasta` y actualiza todas las asignaciones del equipo. Valida `desde ≤ hasta` una vez (la regla aplica al bloque entero). Es todo-o-nada. Emite UN `ASIGNACION_MODIFICAR` con `filas_afectadas` = cantidad de filas tocadas.

### D8 — Auditoría con `filas_afectadas` real del bloque
- Masiva: un `ASIGNACION_CREAR` por alta (reutiliza el camino de `AsignacionService.create`) + un `ASIGNACION_MODIFICAR` de resumen del bloque con `filas_afectadas = creadas`.
- Clonado: igual patrón; `ASIGNACION_MODIFICAR` resumen con `filas_afectadas = clonadas`, `detalle` con tupla origen y destino.
- Vigencia: un solo `ASIGNACION_MODIFICAR` con `filas_afectadas` = filas actualizadas y `detalle` con la nueva vigencia.
- IP / user_agent: se propagan desde el request (no hardcodear "0.0.0.0" como hace el camino de servicio de C-07; el router de equipos pasa los valores reales del `Request`).

### D9 — Export CSV (F4.7): MVP, columnas estables, RFC 4180
Formato CSV con header fijo: `legajo,docente,rol,materia_id,carrera_id,cohorte_id,comisiones,desde,hasta,estado`. Genera `text/csv` con `Content-Disposition: attachment`. `comisiones` se serializa como lista separada por `;` para no chocar con el separador `,`. Sin PII sensible (no DNI/CBU/email) — solo legajo + nombre, igual que `UsuarioMinimo` de C-07. Filtra por tupla de equipo + `tenant_id`.

### D10 — Repository: métodos nuevos de equipo, sin tocar los de C-07
Se agregan a `AsignacionRepository`:
- `list_distinct_equipos(tenant_id, session, **filtros)` → tuplas `(materia, carrera, cohorte)` distintas con conteo (para F4.3 y `GET /equipos`).
- `list_by_equipo(tenant_id, materia_id, carrera_id, cohorte_id, session, solo_vigentes)` → asignaciones de un equipo.
- `bulk_update_vigencia(tenant_id, materia_id, carrera_id, cohorte_id, desde, hasta, session)` → UPDATE masivo, devuelve filas afectadas.
- `exists_vigente(tenant_id, usuario_id, role_id, materia_id, carrera_id, cohorte_id, session)` → para idempotencia de masiva/clonado.

## Risks / Trade-offs

- **[Best-effort en masiva puede confundir]** → la response es explícita (`creadas` + `rechazadas[]` con motivo); el frontend muestra el detalle. Documentado en el spec.
- **[Clonado podría duplicar si se corre dos veces]** → mitigado por D6 (idempotencia vía `exists_vigente`). El clonado es re-ejecutable.
- **[`filas_afectadas` mal contado en el audit invalida la trazabilidad (dominio CRÍTICO)]** → cada operación de bloque cuenta filas explícitamente y lo testea (es regla de negocio → cobertura ≥90%).
- **[Equipo como tupla, no entidad → consultas con 3 columnas]** → mitigado con el índice existente `ix_asignacion_tenant_usuario` y se evalúa agregar índice `(tenant_id, materia_id, carrera_id, cohorte_id)` si el plan lo exige. Como NO hay migración en este change, si se necesita el índice se agrega en un change de optimización aparte (no bloquea C-08).
- **[CSV inyección de fórmulas]** → escapar celdas que empiecen con `=`, `+`, `-`, `@` (prefijo `'`) en el export para evitar CSV injection en Excel.

## Migration Plan

Sin migración de schema (no agrega columnas ni tablas). Despliegue = deploy de código. Rollback = revertir el deploy; no hay cambios de datos estructurales. Las asignaciones creadas por masiva/clonado son `Asignacion` normales y reversibles por soft-delete del CRUD de C-07.

## Open Questions

- Ninguna bloqueante. La semántica de NEXO (PA-25) no afecta a C-08: NEXO tiene `equipos:asignar` en la matriz, así que puede operar equipos; el clonado/masiva valida rol×contexto vía `AsignacionService` que ya acepta NEXO sin contexto requerido.
