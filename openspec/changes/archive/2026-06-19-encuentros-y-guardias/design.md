## Context

C-13 implementa la Épica 6 (F6.1–F6.6) y FL-06. Depende de C-07 (`Asignacion`, `Usuario`) para las FK de actores y de C-06 (`Materia`, `Carrera`, `Cohorte`) para el contexto académico. El sistema ya tiene: el mixin base tenant-scoped (`id`, `tenant_id`, `created_at`, `updated_at`, `deleted_at`) de C-02, el `BaseRepository[T]` que filtra por tenant y `deleted_at IS NULL`, el guard `require_permission(...)` de C-04, y el helper de auditoría de C-05.

El núcleo de C-13 tiene dos sub-dominios independientes:
1. **Encuentros** (slot + instancias): la complejidad radica en la generación automática de instancias a partir de un slot recurrente y en el ciclo de vida independiente de cada instancia.
2. **Guardias**: CRUD con ciclo de estados y export; más simple pero con alcance por rol.

**Nota sobre numeración de migración**: las migraciones 001–007 ya existen (ver `backend/alembic/versions/`). C-13 usa `008_encuentros_y_guardias`. El número se fija como `008` ya que ese slot está libre.

## Goals / Non-Goals

**Goals:**

- Modelos ORM `SlotEncuentro`, `InstanciaEncuentro`, `Guardia` con mixin base y soft delete.
- Lógica de generación de instancias: recurrente (N semanas desde fecha_inicio + dia_semana) o único (fecha_unica → 1 instancia).
- Ciclo de vida de instancia independiente del slot (RN-14): edición de estado, meet_url, video_url, comentario.
- Generación de bloque HTML para embeber en el aula virtual del LMS (F6.4).
- Vista admin de encuentros del tenant (F6.5) con filtros por materia y estado.
- Registro de guardias por tutor (F6.6): alta, cambio de estado, consulta global filtrada, export.
- Endpoints `/api/encuentros/*` y `/api/guardias/*` con guard `encuentros:gestionar`; identidad SIEMPRE desde el JWT.
- Aislamiento multi-tenant en todas las queries.
- Auditoría de eventos significativos.
- Migración `008_encuentros_y_guardias`.

**Non-Goals:**

- Notificaciones push/email al crear encuentros — fuera de alcance (mensajería en C-12).
- Asistencia de alumnos a los encuentros — no modelada en E9/E10/E11.
- Reprogramación masiva de instancias (ej. cambiar hora de todas las instancias de un slot) — aditivo futuro.
- Frontend de encuentros y guardias — C-23.
- Integración directa con el LMS (el export HTML es un fragmento que el docente copia manualmente).

## Decisions

### D-01: Dos modos de slot mutuamente excluyentes (RN-13)

`SlotEncuentro` tiene `cant_semanas` (int ≥ 1) y `fecha_unica` (date, nullable). Son mutuamente excluyentes:
- **Recurrente**: `cant_semanas ≥ 1`, `fecha_unica = NULL`. El service calcula las fechas: `fecha = fecha_inicio + k * 7 días` para k en `[0, cant_semanas)`, donde el día de la semana resulta de `dia_semana` (no se suma offset; `fecha_inicio` debe caer en `dia_semana` — el service valida esto).
- **Único**: `cant_semanas = 0`, `fecha_unica` no nula. Se genera exactamente 1 instancia con esa fecha.

El schema de entrada (`SlotCreate`) tiene campo `modo: Literal["recurrente", "unico"]` más los campos del modo correspondiente. El service valida y rechaza con 422 si la combinación es inválida. Alternativa descartada: dejar ambas columnas nullable y que el cliente mezcle — propenso a estados inconsistentes.

### D-02: Generación de instancias es parte del servicio, no del ORM

La generación de `InstanciaEncuentro` a partir de un `SlotEncuentro` ocurre en `EncuentroService.create_slot(...)`, dentro de la misma transacción: se inserta el slot y luego se insertan las N instancias en bulk (`session.add_all`). Si el slot se borra (soft delete), las instancias no se borran automáticamente — cada instancia tiene su propio ciclo (RN-14). Los slots borrados siguen referenciando instancias vigentes que el docente puede editar.

Alternativa descartada: trigger o listener ORM que genere instancias — acopla lógica de negocio al ORM y dificulta el testing.

### D-03: Instancia editable en campos limitados (RN-14), slot inmutable post-creación

`InstanciaEncuentro` expone solo un endpoint `PATCH` que acepta `estado`, `meet_url`, `video_url` y `comentario`. El resto de campos (fecha, hora, titulo) son read-only post-creación. El slot tampoco es editable post-creación (para no invalidar las instancias ya generadas). Si el docente necesita corregir el horario de un slot, debe crear uno nuevo y cancelar las instancias del anterior.

Alternativa descartada: edición full del slot con re-generación de instancias — conflicto con instancias ya en estado Realizado.

### D-04: Ciclo de estados de `InstanciaEncuentro`

Enum `EstadoInstancia`: `Programado` (inicial), `Realizado`, `Cancelado`. Transiciones válidas:

```
Programado → Realizado | Cancelado
Realizado  → Programado                (corrección, solo COORDINADOR/ADMIN)
Cancelado  → Programado                (reactivar, solo COORDINADOR/ADMIN)
```

El service mantiene `_TRANSICIONES_INSTANCIA` y rechaza con 400 las inválidas. El PROFESOR/TUTOR puede marcar Realizado o Cancelado; solo COORDINADOR/ADMIN pueden revertir. Alternativa descartada: estado libre sin máquina — pierde la semántica de realizado/cancelado.

### D-05: Ciclo de estados de `Guardia`

Enum `EstadoGuardia`: `Pendiente` (inicial al registrar), `Realizada`, `Cancelada`. Transiciones:

```
Pendiente → Realizada | Cancelada
Realizada  → (terminal)
Cancelada  → Pendiente                 (solo COORDINADOR/ADMIN)
```

El TUTOR puede marcar sus propias guardias como Realizada o Cancelada. Solo COORDINADOR/ADMIN pueden revertir a Pendiente.

### D-06: Alcance por rol en el service

Permiso único `encuentros:gestionar`. El service resuelve el alcance según el rol efectivo de la sesión:

- **PROFESOR / TUTOR**: ven y gestionan solo sus propios slots e instancias (derivado de `asignacion_id` → `usuario_id = sesión`). Para guardias, TUTOR gestiona las propias.
- **COORDINADOR / ADMIN**: ven y gestionan todo el tenant.

La vista de instancias (`GET /api/encuentros/instancias`) acepta `materia_id`, `estado`, `fecha_desde`, `fecha_hasta` como query params. Para PROFESOR/TUTOR el service inyecta además el filtro de `asignacion_id`.

Alternativa descartada: permisos separados `encuentros:ver_global` / `encuentros:gestionar_propio` — multiplica la matriz; el alcance es derivable del rol.

### D-07: HTML export para el LMS (F6.4)

`GET /api/encuentros/instancias/{slot_id}/html` devuelve `text/html` (no JSON) con una tabla o lista HTML de instancias ordenadas por fecha. Cada fila incluye: fecha, hora, título, estado, enlace `meet_url` (si programado) y enlace `video_url` (si realizado). El PROFESOR copia el fragmento y lo embebe en el aula virtual. El formato HTML es simple, sin CSS inline excepto estructura básica de tabla.

Alternativa descartada: endpoint que retorne PDF — sobre-ingeniería; el LMS acepta HTML directamente.

### D-08: Export de guardias (F6.6)

`GET /api/guardias/export` retorna CSV con columnas: `fecha_creacion`, `tutor`, `materia`, `carrera`, `cohorte`, `dia`, `horario`, `estado`, `comentarios`. Solo accesible para COORDINADOR/ADMIN (alcance full). El service aplica los mismos filtros del listado. Formato: CSV con `Content-Disposition: attachment; filename="guardias_export.csv"`.

### D-09: Auditoría de eventos significativos

- Crear slot → `ENCUENTRO_SLOT_CREAR` (actor, materia_id, detalle: {slot_id, cant_instancias}).
- Editar instancia → `ENCUENTRO_INSTANCIA_EDITAR` (actor, materia_id, detalle: {instancia_id, campos_editados}).
- Registrar guardia → `GUARDIA_REGISTRAR` (actor, materia_id, detalle: {guardia_id}).
- Cambiar estado de guardia → `GUARDIA_CAMBIAR_ESTADO` (actor, detalle: {guardia_id, estado_anterior, estado_nuevo}).

Crear instancias individuales (como parte del slot) no audita por separado — está cubierto por `ENCUENTRO_SLOT_CREAR` con `cant_instancias` en el detalle.

### D-10: `asignacion_id` como FK en Slot y Guardia

Tanto `SlotEncuentro` como `Guardia` llevan `asignacion_id` (FK → `asignacion.id`) como identifica el KB E9/E11. Esto permite derivar `usuario_id` y `materia_id` desde la asignación. Sin embargo, para evitar queries de join en todos los listados, `materia_id` también se desnormaliza directamente en el modelo (FK → `materia.id`), consistente con E9/E11. El service valida que `asignacion.materia_id == slot.materia_id` al crear.

## Risks / Trade-offs

- **[Riesgo] `fecha_inicio` no cae en `dia_semana`**: el service valida que el día de la semana de `fecha_inicio` coincida con `dia_semana`; si no coincide → 422.
- **[Riesgo] Slots con muchas semanas generan muchas instancias**: no hay límite hard en MVP; documentar recomendación de ≤ 52 semanas en la spec.
- **[Trade-off] Soft delete en slot no propaga a instancias**: la instancia puede seguir siendo editada aunque el slot esté borrado. Es intencional (RN-14) y coherente con el modelo de historia.
- **[Trade-off] Export CSV sin paginación**: aceptable para el volumen esperado de guardias por cuatrimestre; si escala se agrega streaming.

## Migration Plan

1. Agregar `encuentros:gestionar` a la tabla `permiso` (seed en `rbac_seed.py`) y asignarlo a PROFESOR, TUTOR, COORDINADOR y ADMIN en `rol_permiso`.
2. Ejecutar la migración `008_encuentros_y_guardias`: crea `slot_encuentro`, `instancia_encuentro`, `guardia` con FKs, índices de filtro y enums.
3. No hay datos previos que migrar; rollback = `op.drop_table(...)` en orden inverso de FK.

## Open Questions

*(ninguna — C-13 no está bloqueado por preguntas ALTA. Asume `Asignacion`, `Usuario`, `Materia`, `Carrera`, `Cohorte` disponibles de C-07/C-06. El número de migración se fija en 008.)*
