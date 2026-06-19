## ADDED Requirements

### Requirement: Endpoints CRUD de asignaciones bajo permiso equipos:asignar
El sistema SHALL exponer los endpoints `GET /api/v1/asignaciones`, `GET /api/v1/asignaciones/{id}`, `POST /api/v1/asignaciones`, `PUT /api/v1/asignaciones/{id}` y `DELETE /api/v1/asignaciones/{id}` protegidos por el permiso `equipos:asignar`. El `tenant_id` aplicado en cada operación MUST derivarse del JWT del caller; ningún parámetro del request MUST permitir cambiar de tenant. Todo intento de acceso sin el permiso MUST responder 403.

#### Scenario: COORDINADOR crea una asignación
- **WHEN** un caller con permiso `equipos:asignar` envía POST `/api/v1/asignaciones` con un payload válido
- **THEN** la API responde 201 y devuelve el recurso creado, con `tenant_id` igual al del caller

#### Scenario: TUTOR sin permiso rechazado
- **WHEN** un caller con rol TUTOR (sin `equipos:asignar`) envía GET `/api/v1/asignaciones`
- **THEN** la API responde 403

#### Scenario: Tenant aislado en GET
- **WHEN** un COORDINADOR del tenant A solicita GET `/api/v1/asignaciones`
- **THEN** la respuesta contiene únicamente asignaciones del tenant A

### Requirement: Filtros y paginación del listado
El sistema SHALL soportar los siguientes filtros en `GET /api/v1/asignaciones`: `usuario_id`, `materia_id`, `carrera_id`, `cohorte_id`, `rol`, `responsable_id`, `estado_vigencia` (uno de `vigente`, `vencida`, `todas`; default `vigente`). El listado MUST devolver hasta 50 asignaciones por página por defecto, con soporte de paginación por cursor o `offset/limit`.

#### Scenario: Filtro por usuario_id
- **WHEN** un caller solicita GET `/api/v1/asignaciones?usuario_id=U1`
- **THEN** la respuesta contiene únicamente asignaciones de `usuario_id = U1` dentro del tenant del caller

#### Scenario: Filtro estado_vigencia=todas devuelve histórico
- **WHEN** un caller solicita GET `/api/v1/asignaciones?estado_vigencia=todas`
- **THEN** la respuesta incluye asignaciones vigentes Y vencidas (no soft-deleted)

#### Scenario: Default estado_vigencia=vigente
- **WHEN** un caller solicita GET `/api/v1/asignaciones` sin parámetros
- **THEN** la respuesta contiene únicamente asignaciones cuyo `estado_vigencia = "Vigente"`

### Requirement: Soft delete preserva el histórico
El sistema SHALL implementar `DELETE /api/v1/asignaciones/{id}` como soft delete (setea `deleted_at = NOW()`). El registro MUST conservarse y MUST poder ser consultado bajo `?incluir_eliminadas=true` para uso administrativo. La eliminación física NO MUST estar disponible vía API.

#### Scenario: Soft delete responde 204 y preserva
- **WHEN** un caller con `equipos:asignar` ejecuta DELETE `/api/v1/asignaciones/{id}`
- **THEN** la API responde 204 y el registro queda con `deleted_at` no nulo

#### Scenario: Asignación soft-deleted no aparece en listado default
- **WHEN** un caller solicita GET `/api/v1/asignaciones` sin filtros especiales
- **THEN** las asignaciones con `deleted_at` no nulo NO aparecen

#### Scenario: Asignación soft-deleted no otorga permisos
- **WHEN** un usuario tiene una asignación soft-deleted que originalmente otorgaba un rol vigente
- **THEN** el resolver de permisos efectivos NO la considera (no le otorga el rol)

### Requirement: Validación con Pydantic extra='forbid'
El sistema SHALL definir schemas `AsignacionCreate`, `AsignacionUpdate` y `AsignacionResponse` con `model_config = ConfigDict(extra='forbid')`. El `AsignacionResponse` MUST incluir un sub-objeto `usuario` minimal `{id, nombre, apellidos, legajo}` sin PII sensible (no `dni`, `cuil`, `cbu`, `alias_cbu`).

#### Scenario: Campo desconocido rechazado
- **WHEN** un caller envía POST `/api/v1/asignaciones` con un campo extra `prioridad`
- **THEN** la API responde 422 indicando el campo no permitido

#### Scenario: Response no expone PII
- **WHEN** un caller obtiene una asignación
- **THEN** el sub-objeto `usuario` contiene únicamente `id`, `nombre`, `apellidos`, `legajo`; NO contiene `dni`, `cuil`, `cbu`, `alias_cbu` ni `email`

### Requirement: Auditoría de operaciones CRUD de asignaciones
El sistema SHALL registrar en el audit log toda operación exitosa sobre asignaciones con códigos de acción `ASIGNACION_CREAR`, `ASIGNACION_MODIFICAR` y `ASIGNACION_BAJA`. El registro MUST contener el `actor_id`, el `tenant_id`, el `id` de la asignación, el `usuario_id` afectado y el `rol`.

#### Scenario: Crear asignación emite ASIGNACION_CREAR
- **WHEN** un caller crea una asignación exitosamente
- **THEN** la tabla `audit_log` contiene una entrada con `accion = "ASIGNACION_CREAR"` y referencia a la asignación creada

#### Scenario: Soft delete emite ASIGNACION_BAJA
- **WHEN** un caller soft-deletea una asignación
- **THEN** la tabla `audit_log` contiene una entrada con `accion = "ASIGNACION_BAJA"`
