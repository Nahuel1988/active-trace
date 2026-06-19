# Spec: guardia-lifecycle

## Overview

Guard duty registration by tutors with state cycle (Pendiente → Realizada | Cancelada)
and global query/export for coordination (F6.6). Each Guardia is linked to an Asignacion
(TUTOR role) and includes materia, carrera, cohorte, día, horario, and state.
COORDINADOR/ADMIN can query and export all guardias; TUTOR can only manage their own.

## ADDED Requirements

### Requirement: GUA-CREATE-001 — Register a new guardia

The system SHALL allow a user with `encuentros:gestionar` permission to create a `Guardia`
record. The initial state SHALL be `Pendiente`. Required fields: `asignacion_id`,
`materia_id`, `carrera_id`, `cohorte_id`, `dia`, `horario`. The `comentarios` field
SHALL be optional.

#### Scenario: Successful guardia creation

- **WHEN** a TUTOR sends `POST /api/guardias` with valid `asignacion_id`, `materia_id`, `carrera_id`, `cohorte_id`, `dia: "lunes"`, `horario: "14:00–15:00"`
- **THEN** the system returns 201 and the response has `estado: "pendiente"` and a non-null `id`

#### Scenario: Missing required field returns 422

- **WHEN** a user sends `POST /api/guardias` without `horario`
- **THEN** the system returns 422 with a validation error

### Requirement: GUA-OWN-ASIGNACION-002 — TUTOR can only register own guardias

The system SHALL validate that a TUTOR's `asignacion_id` in the guardia matches their
own session identity (derived from JWT). A TUTOR SHALL NOT create a guardia with another
user's `asignacion_id`. COORDINADOR/ADMIN MAY create guardias for any `asignacion_id`
in the tenant.

#### Scenario: TUTOR creates guardia with own asignacion succeeds

- **WHEN** a TUTOR sends `POST /api/guardias` with `asignacion_id` matching their own assignment
- **THEN** the system returns 201

#### Scenario: TUTOR creates guardia with another's asignacion returns 403

- **WHEN** a TUTOR sends `POST /api/guardias` with `asignacion_id` belonging to a different user
- **THEN** the system returns 403 Forbidden

#### Scenario: COORDINADOR creates guardia for any asignacion

- **WHEN** a COORDINADOR sends `POST /api/guardias` with any `asignacion_id` in the tenant
- **THEN** the system returns 201

### Requirement: GUA-STATE-MACHINE-003 — Guardia state transitions (D-05)

The system SHALL enforce the following state machine for `EstadoGuardia`:

```
Pendiente → Realizada | Cancelada
Realizada  → (terminal — no transitions allowed)
Cancelada  → Pendiente                (only COORDINADOR/ADMIN)
```

Invalid transitions SHALL return 400 with a descriptive error.

#### Scenario: Valid transition Pendiente → Realizada

- **WHEN** a TUTOR sends `PATCH /api/guardias/{id}/estado` with `{"estado": "realizada"}` on a guardia in "Pendiente" state
- **THEN** the system returns 200 and the guardia state is "Realizada"

#### Scenario: Valid transition Pendiente → Cancelada

- **WHEN** a TUTOR sends `PATCH /api/guardias/{id}/estado` with `{"estado": "cancelada"}` on a guardia in "Pendiente" state
- **THEN** the system returns 200 and the guardia state is "Cancelada"

#### Scenario: Realizada is terminal — no further transitions allowed

- **WHEN** a user sends `PATCH /api/guardias/{id}/estado` with any estado on a guardia in "Realizada" state
- **THEN** the system returns 400 with an error indicating "Realizada" is a terminal state

### Requirement: GUA-STATE-REVERSION-004 — Revert Cancelada → Pendiente is role-restricted (D-05)

The system SHALL allow only COORDINADOR or ADMIN to revert a "Cancelada" guardia back
to "Pendiente". A TUTOR attempting this SHALL receive 403.

#### Scenario: COORDINADOR reverts Cancelada → Pendiente

- **WHEN** a COORDINADOR sends `PATCH /api/guardias/{id}/estado` with `{"estado": "pendiente"}` on a guardia in "Cancelada" state
- **THEN** the system returns 200 and the guardia state is "Pendiente"

#### Scenario: TUTOR cannot revert Cancelada → Pendiente

- **WHEN** a TUTOR sends `PATCH /api/guardias/{id}/estado` with `{"estado": "pendiente"}` on a guardia in "Cancelada" state
- **THEN** the system returns 403 Forbidden

### Requirement: GUA-SCOPE-005 — Scope by role for guardia operations

The system SHALL enforce access scope: TUTOR can only see and manage their own guardias
(via `asignacion_id`). COORDINADOR and ADMIN can see and manage all guardias in the tenant.

#### Scenario: TUTOR lists own guardias only

- **WHEN** a TUTOR with 2 asignaciones calls `GET /api/guardias`
- **THEN** the response contains only guardias whose `asignacion_id` belongs to that TUTOR

#### Scenario: COORDINADOR lists all guardias

- **WHEN** a COORDINADOR calls `GET /api/guardias`
- **THEN** the response contains all guardias in the tenant

#### Scenario: TUTOR cannot access another user's guardia detail

- **WHEN** a TUTOR requests `GET /api/guardias/{id}` for a guardia belonging to a different user
- **THEN** the system returns 404

### Requirement: GUA-FILTERS-006 — Filter guardia list

The system SHALL support filtering guardias by `materia_id`, `carrera_id`, `cohorte_id`,
`estado`, and `asignacion_id` as query parameters. For TUTOR, the service SHALL
additionally scope results to the tutor's own guardias.

#### Scenario: Filter guardias by estado

- **WHEN** a user calls `GET /api/guardias?estado=realizada`
- **THEN** the response contains only guardias with "Realizada" state

#### Scenario: Filter guardias by materia

- **WHEN** a COORDINADOR calls `GET /api/guardias?materia_id=M1`
- **THEN** the response contains only guardias for materia M1

#### Scenario: Combined filters

- **WHEN** a COORDINADOR calls `GET /api/guardias?materia_id=M1&estado=pendiente&cohorte_id=C1`
- **THEN** the response contains only "Pendiente" guardias for materia M1 in cohorte C1

#### Scenario: Empty result returns empty list

- **WHEN** no guardias match the applied filters
- **THEN** the system returns 200 with `[]`

### Requirement: GUA-EXPORT-CSV-007 — Export guardias as CSV (D-08)

The system SHALL provide a CSV export endpoint `GET /api/guardias/export` accessible
only to COORDINADOR/ADMIN. The CSV SHALL include columns: `fecha_creacion`, `tutor`,
`materia`, `carrera`, `cohorte`, `dia`, `horario`, `estado`, `comentarios`. The response
SHALL have Content-Type `text/csv` and `Content-Disposition: attachment; filename="guardias_export.csv"`.
The same filters as the list endpoint SHALL apply.

#### Scenario: COORDINADOR exports guardias

- **WHEN** a COORDINADOR calls `GET /api/guardias/export`
- **THEN** the system returns 200 with `Content-Type: text/csv` and `Content-Disposition: attachment; filename="guardias_export.csv"`, and the body contains the CSV header row and data rows

#### Scenario: TUTOR cannot export guardias

- **WHEN** a TUTOR calls `GET /api/guardias/export`
- **THEN** the system returns 403 Forbidden

#### Scenario: CSV includes header row even with empty results

- **WHEN** a COORDINADOR calls export with filters matching no guardias
- **THEN** the system returns 200 with CSV containing only the header row and no data rows

#### Scenario: Exported CSV respects filters

- **WHEN** a COORDINADOR calls `GET /api/guardias/export?materia_id=M1&estado=pendiente`
- **THEN** the CSV contains only guardias matching materia M1 and estado Pendiente

### Requirement: GUA-AUDIT-008 — Audit events for guardia lifecycle (D-09)

The system SHALL record audit events for guardia creation and state changes:
- `GUARDIA_REGISTRAR` on creation: detail includes `guardia_id`.
- `GUARDIA_CAMBIAR_ESTADO` on state change: detail includes `guardia_id`, `estado_anterior`, `estado_nuevo`.

#### Scenario: Guardia creation generates audit event

- **WHEN** a TUTOR creates a guardia
- **THEN** a `GUARDIA_REGISTRAR` audit record is created with `guardia_id` in the detail

#### Scenario: State change generates audit event

- **WHEN** a TUTOR changes a guardia from "Pendiente" to "Realizada"
- **THEN** a `GUARDIA_CAMBIAR_ESTADO` audit record is created with `guardia_id`, `estado_anterior: "pendiente"`, and `estado_nuevo: "realizada"`

### Requirement: GUA-TENANT-009 — Tenant isolation for guardias

The system SHALL isolate all guardia data by tenant. A user from tenant A SHALL NOT
access guardias belonging to tenant B. The repository SHALL always filter by `tenant_id`.

#### Scenario: Guardia from tenant A invisible to tenant B user

- **WHEN** a user from tenant B requests `GET /api/guardias/{id}` for a guardia from tenant A
- **THEN** the system returns 404

#### Scenario: Guardia list is scoped to tenant

- **WHEN** a COORDINADOR from tenant A calls `GET /api/guardias`
- **THEN** the response contains only guardias from tenant A, not tenant B
