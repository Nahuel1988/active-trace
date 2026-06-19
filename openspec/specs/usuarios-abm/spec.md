## ADDED Requirements

### Requirement: Endpoint admin para ABM de usuarios del tenant
El sistema SHALL exponer los endpoints `GET /api/v1/admin/usuarios`, `GET /api/v1/admin/usuarios/{id}`, `POST /api/v1/admin/usuarios`, `PUT /api/v1/admin/usuarios/{id}` y `DELETE /api/v1/admin/usuarios/{id}` protegidos por el permiso `usuarios:gestionar`. La identidad del caller MUST derivarse exclusivamente del JWT verificado; el `tenant_id` aplicado en cada operación MUST ser el del caller. Todo intento de acceso sin el permiso `usuarios:gestionar` MUST responder 403 (fail-closed).

#### Scenario: ADMIN crea un usuario completo
- **WHEN** un usuario con permiso `usuarios:gestionar` envía POST `/api/v1/admin/usuarios` con todos los campos válidos
- **THEN** la API responde 201 y devuelve el usuario creado con PII descifrada en el body, y la BD persiste el ciphertext correspondiente

#### Scenario: PROFESOR sin permiso recibe 403
- **WHEN** un usuario con rol PROFESOR (sin `usuarios:gestionar`) envía GET `/api/v1/admin/usuarios`
- **THEN** la API responde 403 sin revelar la existencia de la colección

#### Scenario: Tenant aislado en listado
- **WHEN** un ADMIN del tenant A solicita GET `/api/v1/admin/usuarios`
- **THEN** la respuesta contiene únicamente usuarios cuyo `tenant_id` coincide con el del caller (ningún usuario del tenant B aparece)

#### Scenario: Listado paginado por defecto
- **WHEN** un ADMIN solicita GET `/api/v1/admin/usuarios` sin parámetros
- **THEN** la respuesta devuelve hasta 50 usuarios y un cursor / total para paginar

#### Scenario: Filtros admitidos
- **WHEN** un ADMIN solicita GET `/api/v1/admin/usuarios?regional=Mendoza&facturador=true`
- **THEN** la respuesta contiene únicamente usuarios del tenant del caller que cumplen ambos filtros

### Requirement: PII descifrada sólo en el endpoint admin
El sistema SHALL descifrar y devolver `dni`, `cuil`, `cbu` y `alias_cbu` únicamente en las respuestas de `/api/v1/admin/usuarios/*` (caller con `usuarios:gestionar`). Cualquier otro endpoint que devuelva información de un usuario MUST omitir estos campos o devolverlos como sub-objeto sin PII (`{id, nombre, apellidos, legajo}`).

#### Scenario: Endpoint admin devuelve PII descifrada al ADMIN
- **WHEN** un ADMIN obtiene un usuario vía GET `/api/v1/admin/usuarios/{id}`
- **THEN** la respuesta contiene `dni`, `cuil`, `cbu` y `alias_cbu` en claro

#### Scenario: Endpoint público de usuarios omite PII sensible
- **WHEN** cualquier otro endpoint del sistema devuelve un sub-objeto de usuario (ej. en `/api/v1/asignaciones`)
- **THEN** la respuesta NO contiene `dni`, `cuil`, `cbu` ni `alias_cbu`

### Requirement: Soft delete administrativo
El sistema SHALL implementar `DELETE /api/v1/admin/usuarios/{id}` como soft delete: setea `deleted_at = NOW()` y `is_active = false`. El registro MUST conservarse en la BD para auditoría y para preservar referencias históricas (asignaciones, calificaciones, etc.). Un hard delete NO MUST estar disponible vía API.

#### Scenario: Soft delete preserva el registro
- **WHEN** un ADMIN ejecuta DELETE `/api/v1/admin/usuarios/{id}`
- **THEN** la API responde 204 y el registro permanece en la tabla `user` con `deleted_at` no nulo e `is_active = false`

#### Scenario: Usuario soft-deleted no aparece en listado por defecto
- **WHEN** un ADMIN solicita GET `/api/v1/admin/usuarios` sin filtros especiales
- **THEN** los usuarios soft-deleted NO aparecen en la respuesta

#### Scenario: Asignaciones del usuario soft-deleted se conservan
- **WHEN** un usuario es soft-deleted
- **THEN** sus asignaciones permanecen en la tabla `asignacion` sin modificarse y siguen disponibles para auditoría

### Requirement: Validación con Pydantic extra='forbid'
El sistema SHALL definir schemas `UsuarioCreate`, `UsuarioUpdate` y `UsuarioResponse` con `model_config = ConfigDict(extra='forbid')`. Cualquier campo no declarado en el schema MUST provocar una respuesta 422 con detalle del campo excedente.

#### Scenario: Campo desconocido en POST rechazado
- **WHEN** un ADMIN envía POST `/api/v1/admin/usuarios` con un campo extra `super_admin=true`
- **THEN** la API responde 422 indicando el campo no permitido

#### Scenario: Campos opcionales aceptados en PUT
- **WHEN** un ADMIN envía PUT `/api/v1/admin/usuarios/{id}` con solo `regional` y `facturador`
- **THEN** la API responde 200 y actualiza únicamente esos campos, preservando los demás (incluida la PII)

### Requirement: Auditoría de operaciones del ABM
El sistema SHALL registrar en el audit log (capacidad `audit-log`) toda operación exitosa del ABM admin de usuarios, con códigos de acción `USUARIO_CREAR`, `USUARIO_MODIFICAR` y `USUARIO_BAJA`. El registro MUST contener el `actor_id` (caller), el `tenant_id` y el `id` del usuario afectado, sin exponer PII en el campo `detalle`.

#### Scenario: Crear usuario emite USUARIO_CREAR
- **WHEN** un ADMIN crea un usuario exitosamente
- **THEN** la tabla `audit_log` contiene una nueva entrada con `accion = "USUARIO_CREAR"`, el `actor_id` del ADMIN, el `tenant_id` del tenant y referencia al usuario creado

#### Scenario: Detalle de auditoría no expone PII
- **WHEN** se inspecciona el campo `detalle` de la entrada `USUARIO_CREAR`
- **THEN** el detalle NO contiene los valores en claro de `dni`, `cuil`, `cbu`, `alias_cbu` ni `email`
