## Context

C-16 implementa el workflow de tareas internas de la Épica 8 (F8.1–F8.3) y FL-05. Depende de C-07 (`Usuario`, `Asignacion`) para las FK de actores y de C-06 (`Materia`) para el contexto académico. El sistema ya tiene: el mixin base tenant-scoped (`id`, `tenant_id`, `created_at`, `updated_at`, `deleted_at`) de C-02, el `BaseRepository[T]` que filtra por tenant y `deleted_at IS NULL`, el guard `require_permission(...)` de C-04, y el helper de auditoría de C-05.

A diferencia de un CRUD plano, el núcleo de C-16 es una **máquina de estados** y la **doble trazabilidad de actor** (asignado_a / asignado_por). El módulo es de alto uso (cientos de tareas simultáneas), por lo que los listados deben estar indexados por las columnas de filtro.

**Nota sobre numeración de migración**: hay changes en curso (C-07, programas-y-fechas C-15) que reservan los números intermedios. El número Alembic exacto de C-16 se fija al implementar, encadenado tras el `head` vigente en ese momento. Las tasks lo dejan como `0NN`.

## Goals / Non-Goals

**Goals:**

- Modelos ORM `Tarea` y `ComentarioTarea` con mixin base; `ComentarioTarea` append-only.
- Máquina de estados con transiciones válidas validadas en el service (fail-closed): una transición no declarada se rechaza con 400.
- Alta de tarea, delegación (re-asignación con trazabilidad), cambio de estado, comentarios en hilo.
- "Mis tareas" (filtra por `asignado_a` = usuario de la sesión) y administración global con filtros (asignado, asignador, materia, estado, búsqueda libre).
- Alcance por rol resuelto en el service: PROFESOR ve/gestiona lo propio; COORDINADOR/ADMIN ven/gestionan todo el tenant.
- Endpoints `/api/tareas/*` con guard `tareas:gestionar`; identidad SIEMPRE desde el JWT.
- Aislamiento multi-tenant en todas las queries (vía `BaseRepository`).
- Auditoría de alta, delegación y cambio de estado.
- Migración que crea `tarea` y `comentario_tarea`.

**Non-Goals:**

- Notificaciones push/email al asignar o cambiar estado — fuera de alcance (la comunicación saliente vive en C-12).
- Adjuntos / evidencias con archivos — FL-05 menciona "evidencias" pero el modelo de datos (E12) no contempla archivos; queda diferido.
- SLAs, vencimientos o recordatorios automáticos — no en el modelo.
- Frontend del panel de tareas — C-23.

## Decisions

### D-01: Doble columna de actor con relación auto-referencial a `Usuario`

`Tarea` tiene `asignado_a` (FK → `usuario.id`, quién resuelve) y `asignado_por` (FK → `usuario.id`, quién asigna). Ambas son no-nulas: toda tarea nace con un asignador y un asignado. Esto da la trazabilidad pedida por F8.2/FL-05. Alternativa descartada: una tabla de historial de asignaciones separada — innecesaria para MVP; la delegación actualiza `asignado_a`/`asignado_por` y el evento queda en el `AuditLog` (código `TAREA_DELEGAR`), que es append-only e inmutable.

### D-02: Máquina de estados explícita, validada en el service (fail-closed)

`estado` es enum `EstadoTarea`: `Pendiente` (inicial), `EnProgreso`, `Resuelta`, `Cancelada`. Transiciones válidas:

```
Pendiente   → EnProgreso | Cancelada
EnProgreso  → Resuelta   | Cancelada | Pendiente   (devolver a pendiente)
Resuelta    → EnProgreso                            (reapertura controlada por COORDINADOR/ADMIN)
Cancelada   → (terminal, sin salida)
```

El service mantiene un mapa `_TRANSICIONES: dict[EstadoTarea, set[EstadoTarea]]` y rechaza con 400 cualquier transición no declarada. La reapertura `Resuelta → EnProgreso` solo la permite COORDINADOR/ADMIN (alcance global); el asignado no puede reabrir lo que ya marcó resuelto. Alternativa descartada: estados libres sin máquina — perdería la regla de negocio y permitiría estados incoherentes.

### D-03: Alcance por rol en el service, no permisos separados

Un único permiso `tareas:gestionar` cubre escritura. El alcance se resuelve en el service según el rol efectivo del usuario de la sesión:

- **PROFESOR**: solo tareas donde es `asignado_a` o `asignado_por` (lo "propio", coherente con la matriz §3.3 "✅ propio"). No puede reabrir tareas resueltas.
- **COORDINADOR / ADMIN**: todo el tenant; puede crear, delegar, cambiar estado y reabrir.

El service recibe el conjunto de roles efectivos desde la sesión (no desde la petición) y decide. Alternativa descartada: permisos `tareas:gestionar_propio` / `tareas:gestionar_global` — multiplica la matriz sin necesidad; el alcance es derivable del rol.

### D-04: `ComentarioTarea` append-only (sin update ni delete)

El hilo de comentarios es trazabilidad del workflow: una vez creado, un comentario no se edita ni se borra (consistente con la filosofía append-only del proyecto). El modelo no expone endpoints PUT/DELETE para comentarios. `ComentarioTarea` NO usa soft delete porque nunca se borra. Alternativa descartada: comentarios editables — rompería la trazabilidad del hilo.

### D-05: Filtros del listado global como query params, indexados

`GET /api/tareas` (admin) acepta `asignado_a`, `asignado_por`, `materia_id`, `estado` y `q` (búsqueda libre sobre `descripcion`, ILIKE). Por el alto volumen, se crean índices en `(tenant_id, asignado_a)`, `(tenant_id, asignado_por)`, `(tenant_id, materia_id)` y `(tenant_id, estado)`. El repository compone el `WHERE` dinámicamente, siempre con `tenant_id` y `deleted_at IS NULL` por defecto. Alternativa descartada: cargar todo y filtrar en memoria — inviable con cientos de tareas.

### D-06: `materia_id` y `contexto_id` nullable

`materia_id` es nullable (tarea de nivel institucional cuando es nulo, E12). `contexto_id` es una referencia genérica opcional a otra entidad del dominio (UUID sin FK formal, porque puede apuntar a tipos heterogéneos); se guarda como UUID nullable y su interpretación queda a cargo del consumidor. Alternativa descartada: FK polimórfica formal — sobre-ingeniería para MVP; el `contexto_id` documentado en E12 es deliberadamente laxo.

### D-07: Auditoría de eventos significativos

Alta (`TAREA_CREAR`), delegación (`TAREA_DELEGAR`) y cambio de estado (`TAREA_CAMBIAR_ESTADO`) emiten un registro en el `AuditLog` (C-05) con `actor_id` = usuario de la sesión, `materia_id` (si aplica) y `detalle` JSON (`tarea_id`, estado anterior/nuevo, asignado anterior/nuevo). Crear un comentario NO audita (es contenido del propio hilo, ya trazado por `autor_id`/`creado_at`).

## Risks / Trade-offs

- **[Riesgo] Delegar a un usuario de otro tenant** → El service valida que `asignado_a` pertenezca al mismo tenant antes de asignar/delegar; si no, 400. El `BaseRepository` ya impide leer usuarios cross-tenant. Mitigación cubierta por spec (`tarea-delegation`).
- **[Riesgo] PROFESOR intenta operar tarea ajena** → El service filtra por alcance: un PROFESOR que pide una tarea donde no es asignado_a/asignado_por recibe 404 (no 403, para no filtrar existencia). Cubierto por spec.
- **[Trade-off] `contexto_id` sin FK** → Permite acoplar la tarea a cualquier entidad pero sin integridad referencial garantizada por la DB. Es intencional (E12) y aceptado para MVP; la validación del `contexto_id` queda fuera de C-16.
- **[Trade-off] Alto volumen sin paginación en MVP** → El listado admin se entrega con índices pero sin cursor de paginación en esta iteración. Si el volumen lo exige, se agrega `limit`/`offset` de forma aditiva sin romper el contrato.

## Migration Plan

1. Agregar `tareas:gestionar` a la tabla `permiso` (seed en `rbac_seed.py`) y asignarlo a PROFESOR, COORDINADOR y ADMIN en `rol_permiso`.
2. Ejecutar la migración `0NN_tareas_internas`: crea `tarea` (con FKs a `usuario`, `materia` nullable; índices de filtro) y `comentario_tarea` (FK a `tarea` y `usuario`).
3. No hay datos previos que migrar; rollback = `op.drop_table("comentario_tarea")` y `op.drop_table("tarea")`.

## Open Questions

*(ninguna — C-16 no está bloqueado por preguntas ALTA. Asume `Usuario`/`Materia` disponibles de C-07/C-06. El número de migración se fija al implementar.)*
