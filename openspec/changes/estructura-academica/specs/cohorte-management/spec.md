## ADDED Requirements

### Requirement: Cohorte tiene nombre único por tenant y carrera
Una `Cohorte` pertenece a una `Carrera` dentro de un tenant. El par `(tenant_id, carrera_id, nombre)` es único. El sistema SHALL rechazar la creación o actualización de una cohorte con nombre ya existente en la misma combinación carrera × tenant.

#### Scenario: Crear cohorte con nombre único en la carrera
- **WHEN** un ADMIN envía `POST /api/admin/cohortes` con nombre que no existe para esa carrera en el tenant
- **THEN** el sistema crea la cohorte y retorna 201

#### Scenario: Crear cohorte con nombre duplicado en misma carrera
- **WHEN** un ADMIN envía `POST /api/admin/cohortes` con un nombre que ya existe para la misma `carrera_id` en el tenant
- **THEN** el sistema retorna 400 con mensaje descriptivo de conflicto de unicidad

#### Scenario: El mismo nombre puede usarse en distintas carreras
- **WHEN** la carrera "Tecnicatura A" ya tiene una cohorte llamada "MAR-2026" y el ADMIN crea una cohorte "MAR-2026" para la carrera "Tecnicatura B"
- **THEN** el sistema crea la segunda cohorte sin error

---

### Requirement: Cohorte requiere carrera activa para ser creada
El sistema SHALL rechazar la creación de una cohorte cuya carrera esté en estado `Inactiva`.

#### Scenario: Crear cohorte en carrera activa
- **WHEN** un ADMIN crea una cohorte con `carrera_id` de una carrera `Activa`
- **THEN** el sistema crea la cohorte y retorna 201

#### Scenario: Crear cohorte en carrera inactiva
- **WHEN** un ADMIN intenta crear una cohorte con `carrera_id` de una carrera `Inactiva`
- **THEN** el sistema retorna 400 indicando que la carrera asociada no admite nuevas cohortes

---

### Requirement: Cohorte tiene vigencia temporal opcional
Una cohorte puede tener fechas de `vig_desde` y `vig_hasta`. `vig_hasta` puede ser nulo (cohorte abierta). El sistema SHALL almacenar y retornar estas fechas sin lógica adicional de validación de solapamiento en MVP.

#### Scenario: Crear cohorte con vigencia abierta
- **WHEN** un ADMIN crea una cohorte con `vig_hasta = null`
- **THEN** el sistema la crea correctamente y retorna `vig_hasta: null`

#### Scenario: Crear cohorte con vigencia cerrada
- **WHEN** un ADMIN crea una cohorte con `vig_desde` y `vig_hasta` definidos
- **THEN** el sistema las almacena y retorna en la respuesta

---

### Requirement: Cohorte puede activarse e inactivarse
El estado de una `Cohorte` es `Activa` o `Inactiva`. El sistema SHALL permitir cambiar el estado vía `PUT /api/admin/cohortes/{id}`.

#### Scenario: Inactivar cohorte
- **WHEN** un ADMIN envía `PUT /api/admin/cohortes/{id}` con `estado = "Inactiva"`
- **THEN** el sistema actualiza la cohorte y retorna 200

---

### Requirement: ABM de cohortes requiere permiso `estructura:gestionar`
El sistema SHALL verificar el permiso `estructura:gestionar` en todos los endpoints de cohortes. Sin permiso → 403.

#### Scenario: Usuario sin permiso accede a ABM de cohortes
- **WHEN** un usuario sin `estructura:gestionar` envía cualquier request a `/api/admin/cohortes`
- **THEN** el sistema retorna 403

---

### Requirement: Listado de cohortes está aislado por tenant
El sistema SHALL retornar únicamente las cohortes del tenant del usuario autenticado.

#### Scenario: Aislamiento multi-tenant en cohortes
- **WHEN** un ADMIN del tenant A consulta `GET /api/admin/cohortes`
- **THEN** el sistema retorna solo las cohortes del tenant A

---

### Requirement: Cohorte soporta soft delete
El sistema SHALL implementar borrado lógico vía `deleted_at`.

#### Scenario: Borrar cohorte
- **WHEN** un ADMIN envía `DELETE /api/admin/cohortes/{id}`
- **THEN** el sistema establece `deleted_at` y retorna 204; la cohorte deja de aparecer en el listado

#### Scenario: Cohorte borrada no se recupera por ID
- **WHEN** un ADMIN envía `GET /api/admin/cohortes/{id}` de una cohorte con `deleted_at` poblado
- **THEN** el sistema retorna 404
