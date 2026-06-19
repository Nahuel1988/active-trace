## ADDED Requirements

### Requirement: Delegar una tarea a otro docente con trazabilidad
El sistema SHALL permitir re-asignar una tarea a otro usuario vía `POST /api/tareas/{id}/asignar`. Al delegar, `asignado_a` SHALL pasar a ser el nuevo usuario y `asignado_por` SHALL pasar a ser el usuario de la sesión (JWT) que ejecuta la delegación. El nuevo `asignado_a` SHALL pertenecer al mismo tenant. La delegación SHALL registrarse en el `AuditLog` con código `TAREA_DELEGAR`.

#### Scenario: Delegar a otro docente del tenant
- **WHEN** un PROFESOR asignado a una tarea envía `POST /api/tareas/{id}/asignar` con `asignado_a` de otro usuario del mismo tenant
- **THEN** el sistema actualiza `asignado_a` al nuevo usuario, fija `asignado_por` = el usuario de la sesión, retorna 200 y registra el evento en auditoría

#### Scenario: Delegación conserva trazabilidad del asignador
- **WHEN** el usuario U1 delega a U2 una tarea
- **THEN** la tarea resultante tiene `asignado_a = U2` y `asignado_por = U1`, reflejando quién delegó y a quién

#### Scenario: No delegar a un usuario de otro tenant
- **WHEN** un COORDINADOR del tenant A envía `POST /api/tareas/{id}/asignar` con `asignado_a` de un usuario del tenant B
- **THEN** el sistema retorna 400 sin modificar la tarea

### Requirement: Alcance de delegación según rol
El sistema SHALL resolver el alcance de delegación desde el rol efectivo de la sesión. Un PROFESOR SHALL poder delegar solo tareas en las que es `asignado_a` o `asignado_por`. Un COORDINADOR o ADMIN SHALL poder delegar cualquier tarea del tenant.

#### Scenario: PROFESOR delega tarea propia
- **WHEN** un PROFESOR que es `asignado_a` de una tarea la delega a otro docente
- **THEN** el sistema acepta la delegación y retorna 200

#### Scenario: PROFESOR intenta delegar tarea ajena
- **WHEN** un PROFESOR que NO es `asignado_a` ni `asignado_por` de una tarea intenta `POST /api/tareas/{id}/asignar`
- **THEN** el sistema retorna 404 (no revela existencia de la tarea ajena)
