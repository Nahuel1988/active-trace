# Aviso Management

## ADDED Requirements

### Requirement: Crear aviso
El sistema SHALL permitir a usuarios con permiso `avisos:publicar` crear avisos con los siguientes campos obligatorios: `titulo`, `cuerpo`, `alcance` (Global/PorMateria/PorCohorte/PorRol), `severidad` (Info/Advertencia/Crítico), `inicio_en`, `fin_en`. Campos opcionales: `materia_id`, `cohorte_id`, `rol_destino`, `orden`, `requiere_ack`.

#### Scenario: Creación exitosa
- **WHEN** un usuario con `avisos:publicar` envía POST `/api/avisos` con datos válidos
- **THEN** el sistema retorna 201 con el aviso creado y `activo=true` por defecto

#### Scenario: Creación sin permiso
- **WHEN** un usuario sin `avisos:publicar` envía POST `/api/avisos`
- **THEN** el sistema retorna 403

#### Scenario: Creación con alcance PorMateria sin materia_id
- **WHEN** un usuario envía POST `/api/avisos` con `alcance=PorMateria` y `materia_id=null`
- **THEN** el sistema retorna 422

#### Scenario: Creación cross-tenant
- **WHEN** un usuario del tenant A intenta crear un aviso con `materia_id` del tenant B
- **THEN** el sistema retorna 404

### Requirement: Modificar aviso
El sistema SHALL permitir a usuarios con `avisos:publicar` modificar cualquier campo de un aviso existente, excepto `tenant_id`. Si se desactiva (`activo=false`), el aviso deja de ser visible inmediatamente.

#### Scenario: Modificación exitosa
- **WHEN** un usuario con permiso envía PUT `/api/avisos/{id}` con campos válidos
- **THEN** el sistema retorna 200 con el aviso actualizado

#### Scenario: Modificación de aviso soft-deleted
- **WHEN** un usuario envía PUT `/api/avisos/{id}` sobre un aviso con `deleted_at` no nulo
- **THEN** el sistema retorna 404

### Requirement: Eliminar aviso (soft delete)
El sistema SHALL realizar soft delete de avisos (establecer `deleted_at`).

#### Scenario: Eliminación exitosa
- **WHEN** un usuario con permiso envía DELETE `/api/avisos/{id}`
- **THEN** el sistema retorna 204 y el aviso deja de listarse

### Requirement: Listar avisos (gestión)
El sistema SHALL listar todos los avisos del tenant para gestión (incluyendo inactivos y vencidos).

#### Scenario: Listado de gestión
- **WHEN** un usuario con `avisos:publicar` envía GET `/api/avisos`
- **THEN** el sistema retorna 200 con todos los avisos del tenant (no soft-deleted), ordenados por `orden` ASC y `created_at` DESC

### Requirement: Ver avisos visibles (destinatario)
El sistema SHALL listar los avisos visibles para el usuario autenticado según su rol, asignaciones y la vigencia del aviso (RN-18/20).

#### Scenario: Usuario ve avisos globales
- **WHEN** un usuario autenticado (cualquier rol) envía GET `/api/avisos/visibles`
- **THEN** el sistema retorna 200 con los avisos de alcance Global activos y dentro de vigencia

#### Scenario: Usuario ve avisos por materia
- **WHEN** un usuario asignado a una materia envía GET `/api/avisos/visibles`
- **THEN** el sistema incluye avisos de alcance PorMateria para las materias donde tiene asignación vigente

#### Scenario: Usuario ve avisos por cohorte
- **WHEN** un usuario asignado a una cohorte envía GET `/api/avisos/visibles`
- **THEN** el sistema incluye avisos de alcance PorCohorte para las cohortes donde tiene asignación vigente

#### Scenario: Usuario ve avisos por rol
- **WHEN** un usuario con rol TUTOR envía GET `/api/avisos/visibles`
- **THEN** el sistema incluye avisos de alcance PorRol con `rol_destino=TUTOR`

#### Scenario: Aviso fuera de vigencia no se muestra
- **WHEN** un usuario consulta avisos visibles y existe un aviso fuera de `[inicio_en, fin_en]`
- **THEN** el sistema no incluye ese aviso en la respuesta (RN-18)

#### Scenario: Aviso inactivo no se muestra
- **WHEN** un usuario consulta avisos visibles y existe un aviso con `activo=false`
- **THEN** el sistema no incluye ese aviso

#### Scenario: Aislamiento multi-tenant
- **WHEN** un usuario del tenant A consulta avisos visibles
- **THEN** el sistema solo retorna avisos del tenant A, nunca del tenant B
