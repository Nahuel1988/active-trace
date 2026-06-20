## Why

La coordinación docente necesita un canal de seguimiento operativo entre roles: el COORDINADOR delega trabajo a profesores y tutores, y el equipo responde de forma asincrónica con cambios de estado y comentarios en hilo. Hoy no existe ninguna entidad que registre quién asignó qué a quién, ni el avance de esa tarea, ni su trazabilidad. C-16 cierra ese gap (Épica 8, FL-05) y habilita el panel de coordinación del frontend (C-23). Es un módulo de **alto uso**: la plataforma gestiona varios cientos de tareas en simultáneo durante el período activo.

## What Changes

- Nuevo modelo `Tarea` con doble trazabilidad de actor (`asignado_a` = quién resuelve, `asignado_por` = quién asigna), `estado` (Pendiente / En progreso / Resuelta / Cancelada), `descripcion`, `materia_id` opcional (nivel institucional si es nulo) y `contexto_id` opcional (referencia genérica a otra entidad del dominio).
- Nuevo modelo `ComentarioTarea` (hilo append-only de comentarios por tarea: `autor_id`, `texto`, `creado_at`).
- Máquina de estados explícita con transiciones válidas (RN-NN-T): Pendiente → En progreso / Cancelada; En progreso → Resuelta / Cancelada; estados terminales (Resuelta, Cancelada) son inmutables salvo reapertura controlada.
- Alta de tarea (con asignación inicial), delegación a otro docente (re-asignación con trazabilidad del nuevo asignador/asignado), cambio de estado y comentarios en hilo.
- Vista "mis tareas" (F8.1) filtrada por el usuario autenticado, y administración global con filtros (F8.3): por docente asignado, docente asignador, materia, estado y búsqueda libre.
- Endpoints REST bajo `/api/tareas/*` protegidos con el permiso `tareas:gestionar` (PROFESOR sobre lo propio, COORDINADOR y ADMIN global). Fail-closed.
- Migración Alembic que crea las tablas `tarea` y `comentario_tarea`.
- Soft delete sobre `Tarea` (consistente con el mixin base de C-02); `ComentarioTarea` es append-only.

## Capabilities

### New Capabilities

- `tarea-lifecycle`: Modelo `Tarea` con doble trazabilidad (asignado_a / asignado_por), máquina de estados con transiciones válidas, y aislamiento multi-tenant.
- `tarea-delegation`: Delegación / re-asignación de una tarea a otro docente conservando la trazabilidad de quién delegó y a quién.
- `tarea-comments`: Hilo de comentarios append-only por tarea (workflow asincrónico).
- `tarea-administration`: Vista "mis tareas" (propio) y administración global con filtros (asignado, asignador, materia, estado, búsqueda libre) según permiso del rol.

### Modified Capabilities

*(ninguna — no existen specs previas de tareas internas)*

## Impact

- **Nuevas tablas**: `tarea`, `comentario_tarea` (una migración Alembic; número exacto se fija al implementar, encadenado tras C-07 y demás changes en curso).
- **Nuevos endpoints**: `GET/POST /api/tareas`, `GET/PUT /api/tareas/{id}`, `DELETE /api/tareas/{id}` (soft delete), `POST /api/tareas/{id}/asignar` (delegar), `PATCH /api/tareas/{id}/estado` (transición), `GET/POST /api/tareas/{id}/comentarios`, `GET /api/tareas/mias`.
- **Permiso nuevo**: `tareas:gestionar` — requiere seed en la tabla `permiso` y asignación a PROFESOR, COORDINADOR y ADMIN en `rol_permiso`. El alcance "propio" vs "global" se resuelve en el service según el rol efectivo, no con permisos separados.
- **Dependencia hacia atrás**: C-07 (`Usuario`, `Asignacion`) y C-06 (`Materia`) proveen las FK (`asignado_a`, `asignado_por`, `autor_id`, `materia_id`). La propuesta asume que `Usuario` y `Materia` ya existen como tablas.
- **Dependencia hacia adelante**: C-23 (`frontend-coordinacion`) consume estos endpoints para el panel de tareas.
- **Auditoría**: alta, delegación y transiciones de estado generan registro en el `AuditLog` (C-05) con códigos `TAREA_CREAR`, `TAREA_DELEGAR`, `TAREA_CAMBIAR_ESTADO`.
- **Sin breaking changes**: es la primera vez que estas entidades se definen.
