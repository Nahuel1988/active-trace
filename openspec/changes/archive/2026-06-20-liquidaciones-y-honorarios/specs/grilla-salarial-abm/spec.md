## ADDED Requirements

### Requirement: FINANZAS puede administrar SalarioBase con vigencia temporal
El sistema SHALL permitir al usuario con permiso `liquidaciones:configurar-salarios` realizar operaciones CRUD sobre la tabla `SalarioBase`. Cada registro SHALL contener: rol (PROFESOR|TUTOR|NEXO|COORDINADOR), monto (decimal), desde (fecha), hasta (fecha nullable). El sistema SHALL validar que no exista solapamiento de vigencia para el mismo rol al crear o actualizar un registro.

#### Scenario: Crear SalarioBase exitosamente
- **WHEN** un usuario FINANZAS envía POST /api/v1/grilla/salarios-base con rol=PROFESOR, monto=50000, desde=2026-01-01
- **THEN** el sistema crea el registro y responde 201 con el detalle del SalarioBase

#### Scenario: Rechazar solapamiento de vigencia
- **WHEN** un usuario FINANZAS intenta crear un SalarioBase para rol=PROFESOR con desde=2026-06-01 y existe otro registro vigente para PROFESOR cuyo rango (desde/hasta) se superpone
- **THEN** el sistema responde 409 Conflict con mensaje indicando solapamiento de vigencia

#### Scenario: Actualizar hasta de SalarioBase
- **WHEN** un usuario FINANZAS envía PUT /api/v1/grilla/salarios-base/{id} con hasta=2026-12-31
- **THEN** el sistema actualiza el campo hasta y responde 200 con el registro actualizado

#### Scenario: Eliminar SalarioBase (soft delete)
- **WHEN** un usuario FINANZAS envía DELETE /api/v1/grilla/salarios-base/{id}
- **THEN** el sistema marca el registro como eliminado (soft delete) y responde 204

#### Scenario: Listar SalarioBase con filtros
- **WHEN** un usuario FINANZAS envía GET /api/v1/grilla/salarios-base?rol=PROFESOR
- **THEN** el sistema retorna 200 con lista de registros SalarioBase para ese rol

### Requirement: FINANZAS puede administrar SalarioPlus con vigencia temporal
El sistema SHALL permitir al usuario con permiso `liquidaciones:configurar-salarios` realizar operaciones CRUD sobre la tabla `SalarioPlus`. Cada registro SHALL contener: grupo (texto: PROG|BD|ARQ|MAT|MET), rol (PROFESOR|TUTOR|NEXO|COORDINADOR), descripcion (texto), monto (decimal), desde (fecha), hasta (fecha nullable). El sistema SHALL validar que no exista solapamiento de vigencia para el mismo par (grupo, rol).

#### Scenario: Crear SalarioPlus exitosamente
- **WHEN** un usuario FINANZAS envía POST /api/v1/grilla/salarios-plus con grupo=PROG, rol=PROFESOR, monto=10000, desde=2026-01-01, descripcion="Plus Programación"
- **THEN** el sistema crea el registro y responde 201 con el detalle del SalarioPlus

#### Scenario: Rechazar duplicado de (grupo, rol) vigente
- **WHEN** un usuario FINANZAS intenta crear un SalarioPlus con grupo=BD, rol=TUTOR, desde=2026-03-01 y existe otro registro con mismo (grupo, rol) cuyo rango de vigencia se superpone
- **THEN** el sistema responde 409 Conflict con mensaje indicando solapamiento

#### Scenario: Listar SalarioPlus con filtro por grupo
- **WHEN** un usuario FINANZAS envía GET /api/v1/grilla/salarios-plus?grupo=PROG
- **THEN** el sistema retorna 200 con lista de registros SalarioPlus para ese grupo

#### Scenario: Consultar SalarioPlus vigente en una fecha
- **WHEN** un usuario FINANZAS envía GET /api/v1/grilla/salarios-plus?vigente=2026-06-01
- **THEN** el sistema retorna 200 solo con registros cuyo desde <= 2026-06-01 AND (hasta IS NULL OR hasta >= 2026-06-01)

### Requirement: Catálogo de claves de Plus es configurable por tenant
El sistema SHALL permitir a ADMIN configurar el mapeo materia → clave de Plus (grupo). Las claves disponibles son PROG, BD, ARQ, MAT, MET. No SHALL existir materias sin clave asignada. El mapeo SHALL ser almacenado como configuración del tenant.

#### Scenario: ADMIN asigna clave a materia
- **WHEN** un ADMIN configura la clave PROG para la materia "Programación I"
- **THEN** el sistema almacena el mapeo y lo usa en el cálculo de liquidaciones

#### Scenario: Materia sin clave no existe en catálogo
- **WHEN** se intenta crear o actualizar una materia sin asignarle una clave de Plus
- **THEN** el sistema rechaza la operación con error de validación
