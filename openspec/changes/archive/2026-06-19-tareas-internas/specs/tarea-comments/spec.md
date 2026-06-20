## ADDED Requirements

### Requirement: Comentarios en hilo append-only por tarea
El sistema SHALL permitir agregar comentarios a una tarea vía `POST /api/tareas/{id}/comentarios`. Cada `ComentarioTarea` SHALL registrar `autor_id` (tomado de la sesión JWT, nunca del body), `texto` y `creado_at`. Los comentarios SHALL ser append-only: el sistema NO SHALL exponer edición ni borrado de comentarios.

#### Scenario: Agregar comentario a una tarea
- **WHEN** un usuario con acceso a la tarea envía `POST /api/tareas/{id}/comentarios` con `texto`
- **THEN** el sistema crea el comentario con `autor_id` = el usuario de la sesión y `creado_at` actual, y retorna 201

#### Scenario: autor_id no se acepta desde el body
- **WHEN** un usuario envía `POST /api/tareas/{id}/comentarios` incluyendo un campo `autor_id`
- **THEN** el sistema rechaza con 422 (`extra='forbid'`) y nunca usa ese valor como autor

#### Scenario: No existe endpoint de edición ni borrado de comentarios
- **WHEN** un cliente intenta editar o borrar un comentario existente
- **THEN** el sistema no ofrece ninguna ruta para ello (los comentarios son inmutables)

### Requirement: Listado de comentarios en orden cronológico
El sistema SHALL retornar los comentarios de una tarea vía `GET /api/tareas/{id}/comentarios` ordenados por `creado_at` ascendente, únicamente del tenant del usuario autenticado.

#### Scenario: Leer el hilo completo de una tarea
- **WHEN** un usuario con acceso a la tarea solicita `GET /api/tareas/{id}/comentarios`
- **THEN** el sistema retorna 200 con los comentarios ordenados del más antiguo al más reciente

#### Scenario: Comentarios aislados por tenant
- **WHEN** un usuario del tenant A solicita comentarios de una tarea del tenant B
- **THEN** el sistema retorna 404
