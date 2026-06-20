## ADDED Requirements

### Requirement: Listado de equipos del tenant para coordinación

El sistema SHALL exponer `GET /api/v1/equipos`, protegido por `require_permission("equipos:asignar")`, que lista los equipos del tenant — tuplas distintas `(materia_id, carrera_id, cohorte_id)` — con la cantidad de asignaciones vigentes de cada uno, admitiendo filtros opcionales por `materia_id`, `carrera_id`, `cohorte_id`, `rol` y `responsable_id`. Todas las consultas filtran por el `tenant_id` del JWT por defecto.

#### Scenario: Coordinación lista los equipos del tenant

- **WHEN** un usuario con `equipos:asignar` invoca `GET /api/v1/equipos`
- **THEN** el sistema responde 200 con las tuplas de equipo distintas del tenant y el conteo de asignaciones vigentes de cada una.

#### Scenario: Sin permiso de coordinación se rechaza

- **WHEN** un usuario sin `equipos:asignar` invoca `GET /api/v1/equipos`
- **THEN** el sistema responde 403 (fail-closed).

### Requirement: Asignación masiva de docentes a un equipo

El sistema SHALL exponer `POST /api/v1/equipos/asignacion-masiva`, protegido por `require_permission("equipos:asignar")`, que recibe un bloque `{ usuario_ids[], role_id, materia_id, carrera_id, cohorte_id, comisiones?, responsable_id?, desde, hasta? }` y crea una asignación por cada `usuario_id`, aplicando a cada fila las validaciones de rol×contexto de `AsignacionService`. La operación SHALL ser best-effort: crea las filas válidas y reporta las rechazadas con motivo, sin abortar todo el bloque por un rechazo de validación de una fila. El bloque SHALL ser idempotente: si ya existe una asignación vigente para `(usuario, rol, materia, carrera, cohorte)`, no se duplica.

#### Scenario: Bloque totalmente válido

- **WHEN** un usuario con `equipos:asignar` envía un bloque de 3 docentes con rol PROFESOR y contexto completo (materia, carrera, cohorte) válido
- **THEN** el sistema crea 3 asignaciones, responde 201 con `{ creadas: 3, rechazadas: [] }` y emite un evento de auditoría `ASIGNACION_MODIFICAR` con `filas_afectadas = 3`.

#### Scenario: Bloque parcialmente inválido (best-effort)

- **WHEN** un bloque incluye un docente con rol PROFESOR pero sin `cohorte_id` (contexto inválido para PROFESOR) junto con dos docentes válidos
- **THEN** el sistema crea las 2 asignaciones válidas y responde con `{ creadas: 2, rechazadas: [{ usuario_id, motivo }] }`, indicando el motivo de la fila rechazada, sin revertir las creadas.

#### Scenario: Idempotencia — no duplica asignaciones vigentes existentes

- **WHEN** un bloque incluye un docente que ya tiene una asignación vigente para esa misma tupla `(usuario, rol, materia, carrera, cohorte)`
- **THEN** el sistema no crea un duplicado y lo reporta como omitido, contabilizándolo fuera de `creadas`.

#### Scenario: Aislamiento por tenant en la creación

- **WHEN** se ejecuta una asignación masiva
- **THEN** todas las asignaciones creadas llevan el `tenant_id` del JWT y ninguna referencia entidades de otro tenant.

#### Scenario: Sin permiso se rechaza

- **WHEN** un usuario sin `equipos:asignar` invoca `POST /api/v1/equipos/asignacion-masiva`
- **THEN** el sistema responde 403 y no crea ninguna asignación.

### Requirement: Clonado de equipo entre períodos (RN-12)

El sistema SHALL exponer `POST /api/v1/equipos/clonar`, protegido por `require_permission("equipos:asignar")`, que duplica las asignaciones vigentes de un equipo origen `(materia_id, carrera_id, cohorte_id)` hacia un destino `(carrera_id, cohorte_id)` con una nueva vigencia `desde`/`hasta`. Por cada asignación vigente del origen SHALL copiar `usuario_id`, `role_id`, `comisiones` y `responsable_id`, reescribiendo `carrera_id`, `cohorte_id` y las fechas de vigencia hacia el destino. La operación SHALL ser idempotente: no clona una asignación cuya tupla `(usuario, rol, materia, carrera, cohorte)` ya exista vigente en el destino. Solo las asignaciones vigentes (no vencidas, no soft-deleted) del origen SHALL clonarse.

#### Scenario: Clonado de un equipo completo a una nueva cohorte

- **WHEN** un usuario con `equipos:asignar` clona un equipo origen con 4 asignaciones vigentes hacia una cohorte destino vacía con nueva vigencia
- **THEN** el sistema crea 4 asignaciones en el destino preservando `usuario_id`, `role_id`, `comisiones` y `responsable_id`, con `cohorte_id`/`carrera_id` del destino y `desde`/`hasta` de la nueva vigencia, responde con `{ clonadas: 4, omitidas: [] }` y emite `ASIGNACION_MODIFICAR` con `filas_afectadas = 4` y `detalle` que referencia la tupla origen y destino.

#### Scenario: Clonado re-ejecutable no genera duplicados (idempotencia / solapamiento)

- **WHEN** se ejecuta el clonado dos veces consecutivas hacia el mismo destino
- **THEN** la segunda ejecución no crea duplicados: las asignaciones ya presentes en el destino se reportan en `omitidas` y `clonadas` es 0.

#### Scenario: Solo se clonan asignaciones vigentes del origen

- **WHEN** el equipo origen tiene asignaciones vigentes, vencidas y soft-deleted
- **THEN** el sistema clona únicamente las vigentes; las vencidas y soft-deleted no se copian al destino.

#### Scenario: Aislamiento por tenant en el clonado

- **WHEN** se ejecuta un clonado
- **THEN** el origen y el destino se resuelven dentro del `tenant_id` del JWT y todas las asignaciones creadas llevan ese `tenant_id`.

#### Scenario: Sin permiso se rechaza

- **WHEN** un usuario sin `equipos:asignar` invoca `POST /api/v1/equipos/clonar`
- **THEN** el sistema responde 403 y no clona ninguna asignación.

### Requirement: Modificación de vigencia del equipo en bloque

El sistema SHALL exponer `PATCH /api/v1/equipos/vigencia`, protegido por `require_permission("equipos:asignar")`, que actualiza las fechas `desde`/`hasta` de todas las asignaciones de un equipo `(materia_id, carrera_id, cohorte_id)` en una sola operación atómica (todo-o-nada). El sistema SHALL validar `desde ≤ hasta` cuando ambas estén presentes y SHALL emitir un único evento `ASIGNACION_MODIFICAR` con `filas_afectadas` igual a la cantidad de asignaciones actualizadas.

#### Scenario: Corrimiento de vigencia de todo el equipo

- **WHEN** un usuario con `equipos:asignar` actualiza la vigencia de un equipo con 5 asignaciones a un nuevo rango `desde`/`hasta` válido
- **THEN** el sistema actualiza las 5 asignaciones, responde 200 con `filas_afectadas = 5` y emite un único `ASIGNACION_MODIFICAR` con `filas_afectadas = 5`.

#### Scenario: Rango inválido se rechaza sin tocar datos

- **WHEN** se solicita una vigencia con `desde` posterior a `hasta`
- **THEN** el sistema responde 422, no modifica ninguna asignación y no emite evento de auditoría de modificación.

#### Scenario: Aislamiento por tenant

- **WHEN** se actualiza la vigencia de un equipo
- **THEN** solo se actualizan asignaciones del `tenant_id` del JWT.

#### Scenario: Sin permiso se rechaza

- **WHEN** un usuario sin `equipos:asignar` invoca `PATCH /api/v1/equipos/vigencia`
- **THEN** el sistema responde 403 y no modifica ninguna asignación.
