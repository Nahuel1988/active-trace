## ADDED Requirements

### Requirement: Vista de mis equipos resuelta por identidad de sesión

El sistema SHALL exponer `GET /api/v1/equipos/mis-equipos` que devuelve las asignaciones vigentes del usuario autenticado, agrupadas por la tupla de equipo `(materia_id, carrera_id, cohorte_id)`, derivando la identidad EXCLUSIVAMENTE del JWT verificado (`current_user.id`) y filtrando por el `tenant_id` del JWT. El endpoint NO SHALL aceptar `usuario_id` ni ningún selector de identidad por query, body o header.

#### Scenario: El docente ve solo sus propias asignaciones vigentes

- **WHEN** un usuario autenticado con asignaciones vigentes invoca `GET /api/v1/equipos/mis-equipos`
- **THEN** el sistema responde 200 con las asignaciones cuyo `usuario_id` es igual a `current_user.id` y cuyo `tenant_id` es el del JWT, agrupadas por `(materia_id, carrera_id, cohorte_id)` con su rol, comisiones, vigencia y estado.

#### Scenario: No se puede consultar el equipo de otro usuario por parámetro

- **WHEN** un usuario invoca `GET /api/v1/equipos/mis-equipos?usuario_id=<otro>`
- **THEN** el sistema ignora cualquier `usuario_id` del request y responde con las asignaciones del usuario del JWT, nunca las del `usuario_id` provisto.

#### Scenario: Aislamiento por tenant

- **WHEN** un usuario de tenant A invoca `GET /api/v1/equipos/mis-equipos`
- **THEN** la respuesta no incluye ninguna asignación de un tenant distinto al del JWT, aun si el usuario compartiera id con uno de otro tenant.

#### Scenario: No requiere permiso de coordinación

- **WHEN** un usuario sin el permiso `equipos:asignar` pero con asignaciones vigentes invoca `GET /api/v1/equipos/mis-equipos`
- **THEN** el sistema responde 200 (la vista del equipo propio es un derecho del docente, no una capacidad de coordinación).

#### Scenario: Solo asignaciones vigentes

- **WHEN** un usuario tiene asignaciones vigentes y otras vencidas o soft-deleted e invoca `GET /api/v1/equipos/mis-equipos`
- **THEN** la respuesta incluye únicamente las asignaciones con `estado_vigencia == "Vigente"` y `deleted_at IS NULL`.
