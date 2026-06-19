## ADDED Requirements

### Requirement: Inicio de sesión de impersonación permisada
El sistema SHALL proveer el endpoint `POST /api/auth/impersonate/{user_id}` que permite a un usuario con permiso `impersonacion:usar` obtener un access token distinguible que opera con la identidad del usuario `user_id`. El actor real (quien impersona) MUST quedar registrado en el token y en el audit log. El usuario objetivo MUST pertenecer al mismo tenant del actor.

#### Scenario: Impersonación exitosa
- **WHEN** un ADMIN con `impersonacion:usar` hace POST a `/api/auth/impersonate/{user_id}` con un `user_id` válido del mismo tenant
- **THEN** el endpoint devuelve 200 con un access token que contiene `impersonated=true`, `actor_id` del admin, `sub` del usuario impersonado, y `type=access`

#### Scenario: Impersonación registrada en audit log
- **WHEN** se completa un inicio de impersonación exitoso
- **THEN** existe un registro en `audit_log` con `accion="IMPERSONACION_INICIAR"`, `actor_id` del admin, `impersonado_id` del usuario objetivo

#### Scenario: Sin permiso impersonacion:usar → 403
- **WHEN** un usuario sin el permiso `impersonacion:usar` intenta POST a `/api/auth/impersonate/{user_id}`
- **THEN** el sistema responde 403

#### Scenario: Usuario objetivo de otro tenant → 404
- **WHEN** el `user_id` en la URL no pertenece al mismo tenant del actor
- **THEN** el sistema responde 404 (no revela existencia de usuarios de otros tenants)

#### Scenario: Usuario objetivo inexistente → 404
- **WHEN** el `user_id` en la URL no existe en el sistema
- **THEN** el sistema responde 404

#### Scenario: No se puede impersonar a sí mismo
- **WHEN** un usuario intenta impersonar su propio `user_id`
- **THEN** el sistema responde 400

### Requirement: Fin de sesión de impersonación auditado
El sistema SHALL proveer el endpoint `DELETE /api/auth/impersonate` que registra el fin de una sesión de impersonación activa. Solo puede ser llamado con un token de impersonación activo (`impersonated=true`). El evento MUST quedar registrado en el audit log.

#### Scenario: Fin de impersonación registrado
- **WHEN** un cliente con token de impersonación válido hace DELETE a `/api/auth/impersonate`
- **THEN** el sistema responde 204 y existe un registro en `audit_log` con `accion="IMPERSONACION_FINALIZAR"`, `actor_id` del admin, `impersonado_id` del usuario impersonado

#### Scenario: DELETE con token normal → 400
- **WHEN** se llama a DELETE `/api/auth/impersonate` con un access token sin `impersonated=true`
- **THEN** el sistema responde 400

### Requirement: Sesión de impersonación distinguible
El sistema SHALL asegurar que un token de impersonación sea identificable como tal en cualquier punto del stack. El campo `impersonated: true` en el JWT y el campo `actor_id` MUST estar disponibles en el objeto `CurrentUser` expuesto por `get_current_user`.

#### Scenario: get_current_user expone flag de impersonación
- **WHEN** una request llega con token de impersonación válido
- **THEN** `get_current_user` devuelve un `CurrentUser` con `impersonated=True` y `actor_id` no nulo

#### Scenario: Token normal no tiene flag de impersonación
- **WHEN** una request llega con un access token normal (sin impersonación)
- **THEN** `get_current_user` devuelve `CurrentUser` con `impersonated=False` y `actor_id` igual a `user_id`
