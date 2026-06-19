## ADDED Requirements

### Requirement: Materia tiene código único por tenant (catálogo único ADR-006)
`Materia` es la fuente de verdad del catálogo académico del tenant. El par `(tenant_id, codigo)` es único. El sistema SHALL rechazar la creación o actualización de una materia con código ya existente en el mismo tenant.

#### Scenario: Crear materia con código único
- **WHEN** un ADMIN envía `POST /api/admin/materias` con `codigo` que no existe en el tenant
- **THEN** el sistema crea la materia con estado `Activa` y retorna 201

#### Scenario: Crear materia con código duplicado
- **WHEN** un ADMIN envía `POST /api/admin/materias` con `codigo` que ya existe en el mismo tenant
- **THEN** el sistema retorna 400 con mensaje descriptivo de conflicto de unicidad

#### Scenario: Código único es por tenant (no global)
- **WHEN** el tenant A tiene una materia con `codigo = "PROG_I"` y el tenant B crea una materia con el mismo código
- **THEN** el sistema crea la materia del tenant B sin error

---

### Requirement: Materia puede activarse e inactivarse
El estado de una `Materia` es `Activa` o `Inactiva`. El sistema SHALL permitir cambiar el estado vía `PUT /api/admin/materias/{id}`. El estado inicial al crear es `Activa`.

#### Scenario: Inactivar materia
- **WHEN** un ADMIN envía `PUT /api/admin/materias/{id}` con `estado = "Inactiva"`
- **THEN** el sistema actualiza la materia y retorna 200

#### Scenario: Activar materia previamente inactiva
- **WHEN** un ADMIN envía `PUT /api/admin/materias/{id}` con `estado = "Activa"` sobre una materia inactiva
- **THEN** el sistema actualiza el estado y retorna 200

---

### Requirement: ABM de materias requiere permiso `estructura:gestionar`
El sistema SHALL verificar el permiso `estructura:gestionar` en todos los endpoints de materias. Sin permiso → 403.

#### Scenario: Usuario sin permiso accede a ABM de materias
- **WHEN** un usuario sin `estructura:gestionar` envía cualquier request a `/api/admin/materias`
- **THEN** el sistema retorna 403

#### Scenario: ADMIN accede a listado de materias
- **WHEN** un usuario con rol ADMIN envía `GET /api/admin/materias`
- **THEN** el sistema retorna 200 con la lista de materias del tenant

---

### Requirement: Listado de materias está aislado por tenant
El sistema SHALL retornar únicamente las materias del tenant del usuario autenticado. Una misma materia NO puede existir en más de un tenant (catálogo por tenant).

#### Scenario: Aislamiento multi-tenant en materias
- **WHEN** un ADMIN del tenant A consulta `GET /api/admin/materias`
- **THEN** el sistema retorna solo las materias del tenant A, sin ninguna del tenant B

---

### Requirement: Materia soporta soft delete
El sistema SHALL implementar borrado lógico vía `deleted_at`. Una materia borrada no aparece en los listados normales ni puede usarse como FK en módulos posteriores.

#### Scenario: Borrar materia
- **WHEN** un ADMIN envía `DELETE /api/admin/materias/{id}`
- **THEN** el sistema establece `deleted_at` y retorna 204; la materia deja de aparecer en `GET /api/admin/materias`

#### Scenario: Materia borrada no se recupera por ID
- **WHEN** un ADMIN envía `GET /api/admin/materias/{id}` de una materia con `deleted_at` poblado
- **THEN** el sistema retorna 404
