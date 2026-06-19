## ADDED Requirements

### Requirement: Carrera tiene código único por tenant
Una `Carrera` pertenece a un tenant y se identifica dentro de él por un código corto. El par `(tenant_id, codigo)` es único. El sistema SHALL rechazar cualquier intento de crear o actualizar una carrera con un código que ya existe en el mismo tenant.

#### Scenario: Crear carrera con código único
- **WHEN** un ADMIN envía `POST /api/admin/carreras` con `codigo` que no existe en el tenant
- **THEN** el sistema crea la carrera con estado `Activa` y retorna 201

#### Scenario: Crear carrera con código duplicado
- **WHEN** un ADMIN envía `POST /api/admin/carreras` con `codigo` que ya existe en el mismo tenant
- **THEN** el sistema retorna 400 con mensaje descriptivo de conflicto de unicidad

#### Scenario: Código único es por tenant (no global)
- **WHEN** el tenant A tiene una carrera con `codigo = "TUPAD"` y el tenant B crea una carrera con el mismo código
- **THEN** el sistema crea la carrera del tenant B sin error (los namespaces están aislados)

---

### Requirement: Carrera puede activarse e inactivarse
El estado de una `Carrera` es `Activa` o `Inactiva`. El sistema SHALL permitir cambiar el estado vía `PUT /api/admin/carreras/{id}`. El estado inicial al crear es `Activa`.

#### Scenario: Inactivar carrera
- **WHEN** un ADMIN envía `PUT /api/admin/carreras/{id}` con `estado = "Inactiva"`
- **THEN** el sistema actualiza la carrera y retorna 200

#### Scenario: Activar carrera previamente inactiva
- **WHEN** un ADMIN envía `PUT /api/admin/carreras/{id}` con `estado = "Activa"` sobre una carrera inactiva
- **THEN** el sistema actualiza el estado y retorna 200

---

### Requirement: Carrera inactiva no admite nuevas cohortes abiertas
El sistema SHALL rechazar la creación o activación de una cohorte cuya carrera tenga estado `Inactiva`.

#### Scenario: Intentar crear cohorte en carrera inactiva
- **WHEN** un ADMIN intenta crear una `Cohorte` con `carrera_id` de una carrera `Inactiva`
- **THEN** el sistema retorna 400 indicando que la carrera no admite nuevas cohortes

---

### Requirement: ABM de carreras requiere permiso `estructura:gestionar`
El sistema SHALL verificar el permiso `estructura:gestionar` en todos los endpoints de carreras. Sin el permiso → 403.

#### Scenario: Usuario sin permiso accede a ABM
- **WHEN** un usuario sin el permiso `estructura:gestionar` envía cualquier request a `/api/admin/carreras`
- **THEN** el sistema retorna 403

#### Scenario: ADMIN accede a ABM
- **WHEN** un usuario con rol ADMIN (que tiene `estructura:gestionar`) envía `GET /api/admin/carreras`
- **THEN** el sistema retorna 200 con la lista de carreras del tenant

---

### Requirement: Listado de carreras está aislado por tenant
El sistema SHALL retornar únicamente las carreras del tenant del usuario autenticado.

#### Scenario: Aislamiento multi-tenant en listado
- **WHEN** un ADMIN del tenant A consulta `GET /api/admin/carreras`
- **THEN** el sistema retorna solo las carreras del tenant A, sin ninguna del tenant B

---

### Requirement: Carrera soporta soft delete
El sistema SHALL implementar borrado lógico vía `deleted_at`. Una carrera borrada no aparece en los listados normales.

#### Scenario: Borrar carrera
- **WHEN** un ADMIN envía `DELETE /api/admin/carreras/{id}`
- **THEN** el sistema establece `deleted_at` y retorna 204; la carrera deja de aparecer en `GET /api/admin/carreras`

#### Scenario: Carrera borrada no se recupera por ID
- **WHEN** un ADMIN envía `GET /api/admin/carreras/{id}` de una carrera con `deleted_at` poblado
- **THEN** el sistema retorna 404
