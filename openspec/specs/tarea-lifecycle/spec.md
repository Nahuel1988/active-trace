## Requirements

### Requirement: Alta de tarea con doble trazabilidad de actor
El sistema SHALL crear una `Tarea` con `asignado_a` (quién resuelve), `asignado_por` (quién asigna), `descripcion`, `estado` inicial `Pendiente` y `materia_id`/`contexto_id` opcionales. `asignado_por` SHALL tomarse SIEMPRE de la sesión (JWT), nunca del body. Ambos actores SHALL pertenecer al tenant del usuario autenticado.

#### Scenario: Crear tarea con asignado válido
- **WHEN** un COORDINADOR envía `POST /api/tareas` con `asignado_a` de un usuario del mismo tenant y una `descripcion`
- **THEN** el sistema crea la tarea con `estado = Pendiente`, `asignado_por` = el usuario de la sesión, y retorna 201

#### Scenario: asignado_por no se acepta desde el body
- **WHEN** un COORDINADOR envía `POST /api/tareas` incluyendo un campo `asignado_por` en el body
- **THEN** el sistema rechaza la petición con 422 (schema `extra='forbid'`) y nunca usa ese valor como asignador

#### Scenario: Crear tarea con materia nula (nivel institucional)
- **WHEN** un COORDINADOR envía `POST /api/tareas` sin `materia_id`
- **THEN** el sistema crea la tarea con `materia_id = null` y retorna 201

### Requirement: Aislamiento multi-tenant de tareas
El sistema SHALL operar únicamente sobre tareas del tenant del usuario autenticado. Una tarea de otro tenant NO SHALL ser legible, modificable ni referenciable.

#### Scenario: No leer tarea de otro tenant
- **WHEN** un usuario del tenant A solicita `GET /api/tareas/{id}` de una tarea del tenant B
- **THEN** el sistema retorna 404

#### Scenario: Listado aislado por tenant
- **WHEN** un COORDINADOR del tenant A consulta `GET /api/tareas`
- **THEN** el sistema retorna solo tareas del tenant A, sin ninguna del tenant B

### Requirement: Tarea soporta soft delete
El sistema SHALL implementar borrado lógico de `Tarea` vía `deleted_at`. Una tarea borrada no aparece en listados ni se recupera por ID.

#### Scenario: Borrar tarea
- **WHEN** un COORDINADOR envía `DELETE /api/tareas/{id}`
- **THEN** el sistema establece `deleted_at`, retorna 204 y la tarea deja de aparecer en `GET /api/tareas`

#### Scenario: Tarea borrada no se recupera por ID
- **WHEN** un usuario solicita `GET /api/tareas/{id}` de una tarea con `deleted_at` poblado
- **THEN** el sistema retorna 404

### Requirement: Transiciones de estado válidas (máquina de estados)
El sistema SHALL controlar las transiciones de `estado` vía `PATCH /api/tareas/{id}/estado` según la máquina de estados: `Pendiente → EnProgreso | Cancelada`; `EnProgreso → Resuelta | Cancelada | Pendiente`; `Resuelta → EnProgreso` (reapertura); `Cancelada` es terminal (sin salida). Toda transición no declarada SHALL rechazarse con 400 (fail-closed). El cambio de estado SHALL registrarse en el `AuditLog` con código `TAREA_CAMBIAR_ESTADO`.

#### Scenario: Transición válida Pendiente a EnProgreso
- **WHEN** un usuario con acceso a una tarea `Pendiente` envía `PATCH /api/tareas/{id}/estado` con `estado = EnProgreso`
- **THEN** el sistema actualiza el estado, retorna 200 y registra el evento en auditoría

#### Scenario: Transición inválida es rechazada
- **WHEN** un usuario envía `PATCH /api/tareas/{id}/estado` con `estado = Resuelta` sobre una tarea en estado `Pendiente`
- **THEN** el sistema retorna 400 sin modificar el estado

#### Scenario: Estado Cancelada es terminal
- **WHEN** un usuario envía `PATCH /api/tareas/{id}/estado` sobre una tarea en estado `Cancelada` hacia cualquier otro estado
- **THEN** el sistema retorna 400

#### Scenario: Reapertura de tarea resuelta solo por coordinación
- **WHEN** un COORDINADOR o ADMIN envía `PATCH /api/tareas/{id}/estado` con `estado = EnProgreso` sobre una tarea `Resuelta`
- **THEN** el sistema reabre la tarea y retorna 200

#### Scenario: PROFESOR no puede reabrir una tarea resuelta
- **WHEN** un PROFESOR envía `PATCH /api/tareas/{id}/estado` con `estado = EnProgreso` sobre una tarea `Resuelta`
- **THEN** el sistema retorna 403

### Requirement: Escritura de tareas requiere permiso `tareas:gestionar`
El sistema SHALL verificar el permiso `tareas:gestionar` en todos los endpoints de tareas. Sin permiso explícito → 403 (fail-closed).

#### Scenario: Usuario sin permiso accede a tareas
- **WHEN** un usuario sin `tareas:gestionar` (p. ej. ALUMNO) envía cualquier request a `/api/tareas`
- **THEN** el sistema retorna 403

#### Scenario: COORDINADOR con permiso lista tareas
- **WHEN** un usuario con rol COORDINADOR envía `GET /api/tareas`
- **THEN** el sistema retorna 200 con las tareas del tenant
