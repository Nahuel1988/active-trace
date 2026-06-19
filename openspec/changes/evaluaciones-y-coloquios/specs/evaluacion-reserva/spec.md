## ADDED Requirements

### Requirement: Reserva de turno por ALUMNO en día disponible con cupo

El sistema SHALL exponer `POST /api/coloquios/{id}/reservas`, protegido por `require_permission("coloquios:reservar")` (ALUMNO), que permite a un ALUMNO (autenticado vía JWT) reservar un turno en una convocatoria activa. El body SHALL incluir `fecha_hora` dentro de la ventana definida por `dias_disponibles` de la Evaluacion. El sistema SHALL verificar que: (a) el ALUMNO sea candidato habilitado de la convocatoria, (b) no tenga ya una reserva Activa en la misma convocatoria, (c) haya cupo disponible (reservas Activas < `dias_disponibles`). El control de cupo SHALL usar `SELECT FOR UPDATE` según D1 para prevenir condición de carrera. La reserva se crea con estado `Activa`.

#### Scenario: Reserva exitosa con cupo disponible

- **WHEN** un ALUMNO candidato envía `POST /api/coloquios/{id}/reservas` con `fecha_hora` válida y hay cupo disponible
- **THEN** el sistema crea la reserva con estado `Activa`, resta el cupo y responde 201

#### Scenario: ALUMNO no candidato no puede reservar

- **WHEN** un ALUMNO que NO está en el padrón de candidatos envía `POST /api/coloquios/{id}/reservas`
- **THEN** el sistema responde 403 y no crea la reserva

#### Scenario: ALUMNO ya tiene reserva activa en la misma convocatoria

- **WHEN** un ALUMNO que ya tiene una reserva Activa en la convocatoria intenta reservar otro turno
- **THEN** el sistema responde 409 (conflicto) y no crea la segunda reserva

#### Scenario: Sin cupo disponible se rechaza

- **WHEN** un ALUMNO intenta reservar cuando las reservas Activas igualan o superan `dias_disponibles`
- **THEN** el sistema responde 409 con mensaje "Cupo agotado" y no crea la reserva

#### Scenario: ALUMNO no puede reservar en convocatoria de otro tenant

- **WHEN** un ALUMNO del tenant A envía `POST /api/coloquios/{id}/reservas` sobre una convocatoria del tenant B
- **THEN** el sistema responde 404

#### Scenario: Sin permiso `coloquios:reservar` se rechaza

- **WHEN** un COORDINADOR (que no tiene `coloquios:reservar`) envía `POST /api/coloquios/{id}/reservas`
- **THEN** el sistema responde 403

#### Scenario: Fecha_hora fuera de la ventana se rechaza

- **WHEN** un ALUMNO envía `POST /api/coloquios/{id}/reservas` con `fecha_hora` que excede los días desde la creación de la convocatoria según `dias_disponibles`
- **THEN** el sistema responde 422

#### Scenario: Identidad siempre desde la sesión

- **WHEN** un ALUMNO envía `POST /api/coloquios/{id}/reservas` incluyendo un campo `alumno_id` en el body
- **THEN** el sistema responde 422 (Pydantic `extra='forbid'`) y el `alumno_id` se toma del JWT, no del body

### Requirement: Cancelación de reserva por ALUMNO

El sistema SHALL exponer `PATCH /api/coloquios/{id}/reservas/{reserva_id}/cancelar`, protegido por `require_permission("coloquios:reservar")`, que permite al ALUMNO (propietario de la reserva) cancelar su propia reserva. La transición SHALL ser `Activa → Cancelada`. Al cancelar, el cupo se libera (se decrementa el contador de reservas Activas). Una reserva Cancelada NO SHALL poder reactivarse. Solo el ALUMNO propietario o un usuario con `coloquios:gestionar` SHALL poder cancelar una reserva.

#### Scenario: ALUMNO cancela su propia reserva activa

- **WHEN** un ALUMNO envía `PATCH /api/coloquios/{id}/reservas/{reserva_id}/cancelar` sobre su propia reserva Activa
- **THEN** el sistema cambia el estado a `Cancelada`, libera el cupo y responde 200

#### Scenario: ALUMNO no puede cancelar reserva de otro alumno

- **WHEN** un ALUMNO envía `PATCH /api/coloquios/{id}/reservas/{reserva_id}/cancelar` sobre una reserva de otro ALUMNO
- **THEN** el sistema responde 403

#### Scenario: COORDINADOR puede cancelar cualquier reserva del tenant

- **WHEN** un COORDINADOR envía `PATCH /api/coloquios/{id}/reservas/{reserva_id}/cancelar` sobre una reserva de cualquier ALUMNO del tenant
- **THEN** el sistema cambia el estado a `Cancelada` y responde 200

#### Scenario: Cancelar reserva ya cancelada se rechaza

- **WHEN** un ALUMNO envía `PATCH /api/coloquios/{id}/reservas/{reserva_id}/cancelar` sobre una reserva ya en estado `Cancelada`
- **THEN** el sistema responde 400 y no modifica el estado

### Requirement: Control de concurrencia en reserva de cupos (D1)

El sistema SHALL prevenir condiciones de carrera cuando múltiples ALUMNOs reservan simultáneamente sobre la misma convocatoria. El repositorio SHALL ejecutar `SELECT count(*) ... FOR UPDATE` sobre las reservas Activas de la convocatoria dentro de la misma transacción antes de insertar una nueva reserva, asegurando que dos reservas concurrentes no excedan el cupo.

#### Scenario: Dos reservas simultáneas no exceden el cupo

- **WHEN** dos ALUMNOs reservan simultáneamente sobre la misma convocatoria con exactamente 1 cupo libre
- **THEN** una reserva se crea con estado `Activa` y la otra responde 409 "Cupo agotado"

#### Scenario: Transacción con FOR UPDATE no deja reservas huérfanas

- **WHEN** ocurre un error (ej. violación de unicidad) durante la creación de la reserva
- **THEN** la transacción se revierte y el cupo no se descuenta

### Requirement: Mis reservas — consulta del ALUMNO

El sistema SHALL exponer `GET /api/coloquios/mis-reservas`, protegido por `require_permission("coloquios:reservar")`, que retorna las reservas del ALUMNO autenticado (identidad desde JWT) con datos de la convocatoria (materia, instancia, fecha_hora, estado). SHALL admitir filtro opcional por estado (`Activa` | `Cancelada`).

#### Scenario: ALUMNO consulta sus reservas activas

- **WHEN** un ALUMNO consulta `GET /api/coloquios/mis-reservas?estado=Activa`
- **THEN** el sistema retorna 200 solo con sus reservas en estado Activa

#### Scenario: ALUMNO consulta todas sus reservas sin filtro

- **WHEN** un ALUMNO consulta `GET /api/coloquios/mis-reservas`
- **THEN** el sistema retorna 200 con todas sus reservas (Activas y Canceladas)

#### Scenario: ALUMNO ve reservas de otro tenant aisladas

- **WHEN** un ALUMNO consulta `GET /api/coloquios/mis-reservas`
- **THEN** el sistema retorna solo reservas del tenant del JWT, sin reservas de otros tenants aunque sean del mismo usuario_id
