# Spec: instancia-encuentro-edit

## Overview

Per-instance editing of estado, meet_url, video_url, and comentario (RN-14).
Each instance has an independent lifecycle from its parent slot. The state machine
(Programado → Realizado | Cancelado) enforces valid transitions. Reversal of states
(Realizado → Programado, Cancelado → Programado) is restricted to COORDINADOR/ADMIN only.

## ADDED Requirements

### Requirement: INST-EDIT-001 — Edit allowed fields on an instance

The system SHALL allow modifying `estado`, `meet_url`, `video_url`, and `comentario`
on an existing `InstanciaEncuentro`. The PATCH request SHALL accept a partial payload
where at least one field is provided. Fields not present in the payload SHALL remain unchanged.

#### Scenario: Successful edit of multiple fields

- **WHEN** a PROFESOR sends PATCH to `/api/encuentros/instancias/{id}` with `{"meet_url": "https://meet.example.com/new", "comentario": "Clase repaso"}`
- **THEN** the system returns 200 and the response contains the updated `meet_url` and `comentario`; other fields (fecha, hora, titulo, video_url) remain unchanged

#### Scenario: Edit with no fields returns 422

- **WHEN** a user sends PATCH to `/api/encuentros/instancias/{id}` with empty payload `{}`
- **THEN** the system returns 422 because at least one editable field is required

#### Scenario: Edit with read-only fields is silently ignored or rejected

- **WHEN** a user sends PATCH with `{"fecha": "2026-05-01"}`
- **THEN** the system either returns 422 (field not recognized as editable) or ignores the field and returns 200 with the unchanged `fecha`

### Requirement: INST-STATE-MACHINE-002 — Instance state machine (D-04)

The system SHALL enforce the following state machine for `EstadoInstancia`:

```
Programado → Realizado | Cancelado
Realizado  → Programado          (only COORDINADOR/ADMIN)
Cancelado  → Programado          (only COORDINADOR/ADMIN)
```

Invalid transitions SHALL return 400 with a descriptive error.

#### Scenario: Valid transition Programado → Realizado

- **WHEN** a PROFESOR sends PATCH to `/api/encuentros/instancias/{id}` with `{"estado": "realizado"}` on an instance in "Programado" state
- **THEN** the system returns 200 and the instance state is "Realizado"

#### Scenario: Valid transition Programado → Cancelado

- **WHEN** a TUTOR sends PATCH with `{"estado": "cancelado"}` on an instance in "Programado" state
- **THEN** the system returns 200 and the instance state is "Cancelado"

#### Scenario: Invalid transition Cancelado → Realizado returns 400

- **WHEN** a user sends PATCH with `{"estado": "realizado"}` on an instance in "Cancelado" state
- **THEN** the system returns 400 with an error indicating the transition is not allowed

#### Scenario: Invalid transition Realizado → Cancelado returns 400

- **WHEN** a user sends PATCH with `{"estado": "cancelado"}` on an instance in "Realizado" state
- **THEN** the system returns 400 with an error indicating the transition is not allowed

### Requirement: INST-STATE-REVERSION-003 — State reversion is role-restricted (D-04)

The system SHALL allow only COORDINADOR or ADMIN to revert a "Realizado" or "Cancelado"
instance back to "Programado". PROFESOR and TUTOR attempting this SHALL receive 403.

#### Scenario: COORDINADOR reverts Realizado → Programado

- **WHEN** a COORDINADOR sends PATCH with `{"estado": "programado"}` on an instance in "Realizado" state
- **THEN** the system returns 200 and the instance state is "Programado"

#### Scenario: PROFESOR cannot revert Realizado → Programado

- **WHEN** a PROFESOR sends PATCH with `{"estado": "programado"}` on an instance in "Realizado" state
- **THEN** the system returns 403 Forbidden

#### Scenario: COORDINADOR reverts Cancelado → Programado

- **WHEN** a COORDINADOR sends PATCH with `{"estado": "programado"}` on an instance in "Cancelado" state
- **THEN** the system returns 200 and the instance state is "Programado"

### Requirement: INST-SCOPE-004 — Scope by role for instance operations

The system SHALL enforce access scope: PROFESOR and TUTOR can only see and edit instances
derived from their own slots (via `asignacion_id`). COORDINADOR and ADMIN can see and edit
all instances in the tenant.

#### Scenario: PROFESOR edits only own instance

- **WHEN** a PROFESOR sends PATCH to an instance belonging to their own slot
- **THEN** the system returns 200

#### Scenario: PROFESOR cannot edit another user's instance

- **WHEN** a PROFESOR sends PATCH to an instance belonging to a different user
- **THEN** the system returns 404

#### Scenario: COORDINADOR edits any instance in the tenant

- **WHEN** a COORDINADOR sends PATCH to an instance belonging to any user in the tenant
- **THEN** the system returns 200

### Requirement: INST-TENANT-005 — Tenant isolation for instances

The system SHALL isolate all instance data by tenant. A user from tenant A SHALL NOT
access instances belonging to tenant B.

#### Scenario: Instance from tenant A is invisible to tenant B

- **WHEN** a user from tenant B requests PATCH on an instance from tenant A
- **THEN** the system returns 404

### Requirement: INST-LIST-FILTERS-006 — List instances with filters

The system SHALL support filtering instances by `materia_id`, `estado`, `fecha_desde`,
and `fecha_hasta` as query parameters. For PROFESOR/TUTOR, the service SHALL additionally
restrict results to instances derived from their own slots.

#### Scenario: Filter instances by estado

- **WHEN** a COORDINADOR calls `GET /api/encuentros/instancias?estado=programado`
- **THEN** the response contains only instances with "Programado" state

#### Scenario: Filter instances by date range

- **WHEN** a user calls `GET /api/encuentros/instancias?fecha_desde=2026-03-01&fecha_hasta=2026-03-31`
- **THEN** the response contains only instances whose `fecha` falls within the range

#### Scenario: PROFESOR filtered list is scoped to own slots

- **WHEN** a PROFESOR calls `GET /api/encuentros/instancias` without filters
- **THEN** the response contains only instances from slots where `asignacion_id` belongs to that PROFESOR

#### Scenario: Empty result returns empty list (not 404)

- **WHEN** no instances match the applied filters
- **THEN** the system returns 200 with an empty list `[]`

### Requirement: INST-AUDIT-007 — Audit event on instance edit (D-09)

The system SHALL record an audit event `ENCUENTRO_INSTANCIA_EDITAR` when an instance
is modified. The audit detail SHALL include `instancia_id` and the set of changed fields
(`campos_editados`).

#### Scenario: State change generates audit event

- **WHEN** a user edits `estado` on an instance
- **THEN** an `ENCUENTRO_INSTANCIA_EDITAR` audit record is created with `instancia_id` and `campos_editados` containing `["estado"]`

#### Scenario: Multiple field edit generates single audit event

- **WHEN** a user edits both `meet_url` and `comentario` in one request
- **THEN** a single `ENCUENTRO_INSTANCIA_EDITAR` audit record is created with `campos_editados` containing `["meet_url", "comentario"]`
