# Spec: slot-encuentro-lifecycle

## Overview

Creation of recurrent and unique encounter slots with automatic instance generation (RN-13).
A recurrent slot generates N instances (one per week); a unique slot generates exactly 1 instance.
The slot is immutable post-creation; only soft delete is allowed. Instance generation is part of the service
layer and runs atomically within the same transaction.

## ADDED Requirements

### Requirement: SLOT-RECURRENTE-001 — Create recurrent slot with automatic instance generation

The system SHALL generate `cant_semanas` instances when a slot is created in `recurrente` mode.
Each instance date SHALL be `fecha_inicio + k * 7 days` for k in `[0, cant_semanas)`.
The day of the week of `fecha_inicio` SHALL match the slot's `dia_semana` value.

#### Scenario: Create recurrent slot generates N instances

- **WHEN** a PROFESOR or COORDINADOR creates a slot with `modo: "recurrente"`, `cant_semanas: 8`, `fecha_inicio: "2026-03-02"`, `dia_semana: "lunes"`
- **THEN** the system returns 201 and the slot contains exactly 8 `InstanciaEncuentro` records with dates 2026-03-02, 2026-03-09, …, 2026-04-20

#### Scenario: fecha_inicio does not match dia_semana returns 422

- **WHEN** a user creates a recurrent slot with `fecha_inicio: "2026-03-03"` (martes) and `dia_semana: "lunes"`
- **THEN** the system returns 422 with a validation error indicating `fecha_inicio` must fall on the configured `dia_semana`

#### Scenario: Recurrent slot with cant_semanas=1 generates 1 instance

- **WHEN** a user creates a recurrent slot with `cant_semanas: 1`, `fecha_inicio: "2026-03-02"`, `dia_semana: "lunes"`
- **THEN** the system returns 201 and the slot contains exactly 1 instance with date 2026-03-02

### Requirement: SLOT-UNICO-002 — Create unique slot with single instance

The system SHALL generate exactly 1 instance when a slot is created in `unico` mode.
The instance date SHALL be the `fecha_unica` value. `cant_semanas` SHALL be 0.
`fecha_unica` SHALL NOT be null when `modo: "unico"`.

#### Scenario: Create unique slot generates 1 instance

- **WHEN** a user creates a slot with `modo: "unico"`, `fecha_unica: "2026-04-15"`, `dia_semana: "miercoles"`
- **THEN** the system returns 201 and the slot contains exactly 1 instance with date 2026-04-15

#### Scenario: Unique slot with missing fecha_unica returns 422

- **WHEN** a user creates a slot with `modo: "unico"` and `fecha_unica: null`
- **THEN** the system returns 422 with a validation error indicating `fecha_unica` is required for unique mode

### Requirement: SLOT-MODO-VALIDATION-003 — Mode fields are mutually exclusive

The system SHALL validate that `modo` field is `"recurrente"` or `"unico"`. For `recurrente`:
`cant_semanas` SHALL be ≥ 1, `fecha_unica` SHALL be null. For `unico`: `cant_semanas`
SHALL be 0, `fecha_unica` SHALL NOT be null. Invalid combinations SHALL return 422.

#### Scenario: Recurrent mode with fecha_unica set returns 422

- **WHEN** a user creates a slot with `modo: "recurrente"`, `cant_semanas: 4`, and `fecha_unica: "2026-04-15"`
- **THEN** the system returns 422 because `fecha_unica` must be null for recurrent mode

#### Scenario: Unique mode with cant_semanas > 0 returns 422

- **WHEN** a user creates a slot with `modo: "unico"`, `fecha_unica: "2026-04-15"`, and `cant_semanas: 3`
- **THEN** the system returns 422 because `cant_semanas` must be 0 for unique mode

### Requirement: SLOT-IMMUTABLE-004 — Slot is immutable post-creation

The system SHALL NOT provide an endpoint to modify slot fields (titulo, hora, dia_semana, etc.)
after creation. The only lifecycle operation on a slot SHALL be soft delete. If a user
needs to correct slot data, they SHALL create a new slot and cancel the instances of the old one.

#### Scenario: No PATCH/PUT endpoint for slot exists

- **WHEN** a client sends a PATCH request to `/api/encuentros/slots/{id}`
- **THEN** the system returns 405 Method Not Allowed

#### Scenario: Soft delete a slot succeeds

- **WHEN** a user sends DELETE to `/api/encuentros/slots/{slot_id}` for a slot they own (or any slot if COORDINADOR/ADMIN)
- **THEN** the system returns 204 and the slot's `deleted_at` is set to the current timestamp

### Requirement: SLOT-SCOPE-005 — Scope by role for slot operations

The system SHALL enforce access scope: PROFESOR and TUTOR can only see and manage
slots where `asignacion_id` belongs to them. COORDINADOR and ADMIN can see and manage
all slots in the tenant.

#### Scenario: PROFESOR lists only own slots

- **WHEN** a PROFESOR with two asignaciones in the tenant calls `GET /api/encuentros/slots`
- **THEN** the response contains only slots whose `asignacion_id` belongs to that PROFESOR (derived from session JWT)

#### Scenario: COORDINADOR lists all slots in the tenant

- **WHEN** a COORDINADOR calls `GET /api/encuentros/slots`
- **THEN** the response contains all slots from the tenant, regardless of `asignacion_id`

#### Scenario: PROFESOR cannot access another user's slot detail

- **WHEN** a PROFESOR requests `GET /api/encuentros/slots/{slot_id}` where the slot belongs to a different user
- **THEN** the system returns 404

### Requirement: SLOT-TENANT-006 — Tenant isolation for slots

The system SHALL isolate all slot data by tenant. A user from tenant A SHALL NOT see slots
belonging to tenant B. The repository SHALL always filter by `tenant_id` from the session.

#### Scenario: Slot from tenant A is invisible to tenant B

- **WHEN** a user from tenant B requests `GET /api/encuentros/slots/{slot_id}` where the slot belongs to tenant A
- **THEN** the system returns 404

### Requirement: SLOT-AUDIT-007 — Audit event on slot creation

The system SHALL record an audit event `ENCUENTRO_SLOT_CREAR` when a slot is created.
The audit detail SHALL include `slot_id` and `cant_instancias`. Creating the individual
instances SHALL NOT generate separate audit events.

#### Scenario: Creating a recurrent slot generates audit event

- **WHEN** a user creates a recurrent slot with 8 instances
- **THEN** an `ENCUENTRO_SLOT_CREAR` audit record is created with `slot_id` and `cant_instancias: 8`

#### Scenario: Creating a unique slot generates audit event

- **WHEN** a user creates a unique slot with 1 instance
- **THEN** an `ENCUENTRO_SLOT_CREAR` audit record is created with `slot_id` and `cant_instancias: 1`

### Requirement: SLOT-SOFTDELETE-INSTANCES-008 — Soft-deleted slot leaves instances intact

When a slot is soft-deleted, its instances SHALL remain in the database with their current state.
The instances SHALL remain editable (estado, meet_url, video_url, comentario) even after the
slot is deleted. The slot SHALL still be referenceable by existing instances.

#### Scenario: Instances remain editable after slot deletion

- **WHEN** a slot with 3 instances (one in "Realizado" state) is soft-deleted
- **THEN** the instances still exist and `PATCH /api/encuentros/instancias/{id}` on any of them still succeeds
