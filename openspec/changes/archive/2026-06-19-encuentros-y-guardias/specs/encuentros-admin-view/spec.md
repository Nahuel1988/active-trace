# Spec: encuentros-admin-view

## Overview

Cross-sectional view of all encounters in the tenant for COORDINADOR/ADMIN (F6.5).
This capability provides a global list of `InstanciaEncuentro` records with filters
by materia and estado, without the per-user scope restriction that applies to PROFESOR/TUTOR.
It is accessed via the same `GET /api/encuentros/instancias` endpoint but with full
tenant-wide scope when the authenticated user has COORDINADOR or ADMIN role.

## ADDED Requirements

### Requirement: ADMIN-VIEW-001 — COORDINADOR/ADMIN sees all instances in the tenant

The system SHALL return all instances in the tenant when the authenticated user holds
COORDINADOR or ADMIN role, regardless of which `asignacion_id` created the slot.
No `asignacion_id` filter SHALL be applied.

#### Scenario: COORDINADOR lists all instances

- **WHEN** a COORDINADOR calls `GET /api/encuentros/instancias` in a tenant with 3 slots belonging to 3 different PROFESORes
- **THEN** the response contains instances from all 3 slots

#### Scenario: ADMIN lists all instances

- **WHEN** an ADMIN calls `GET /api/encuentros/instancias`
- **THEN** the response contains all instances in the tenant regardless of creator

#### Scenario: PROFESOR sees only own instances via same endpoint

- **WHEN** a PROFESOR calls `GET /api/encuentros/instancias` in the same tenant
- **THEN** the response contains only instances from slots where `asignacion_id` belongs to that PROFESOR

### Requirement: ADMIN-VIEW-002 — Filter by materia_id

The system SHALL support filtering instances by `materia_id` when the caller is
COORDINADOR or ADMIN. The service SHALL return only instances for the specified materia.

#### Scenario: COORDINADOR filters by materia

- **WHEN** a COORDINADOR calls `GET /api/encuentros/instancias?materia_id=M1` where M1 has 5 instances and M2 has 3 instances
- **THEN** the response contains only the 5 instances for materia M1

### Requirement: ADMIN-VIEW-003 — Filter by estado

The system SHALL support filtering instances by `estado` (Programado, Realizado, Cancelado)
for COORDINADOR/ADMIN. The service SHALL apply the filter across all instances in the tenant.

#### Scenario: COORDINADOR filters by estado

- **WHEN** a COORDINADOR calls `GET /api/encuentros/instancias?estado=cancelado`
- **THEN** the response contains only instances with estado "Cancelado" across all slots

### Requirement: ADMIN-VIEW-004 — Filter by date range

The system SHALL support filtering instances by `fecha_desde` and `fecha_hasta` for
COORDINADOR/ADMIN, returning instances whose `fecha` falls within the specified range.

#### Scenario: COORDINADOR filters by date range

- **WHEN** a COORDINADOR calls `GET /api/encuentros/instancias?fecha_desde=2026-04-01&fecha_hasta=2026-04-30`
- **THEN** the response contains only instances whose `fecha` falls in April 2026

### Requirement: ADMIN-VIEW-005 — Combined filters

The system SHALL support combining multiple filters (materia_id, estado, fecha_desde,
fecha_hasta) in a single request. The service SHALL apply all provided filters with AND
semantics.

#### Scenario: Combined filters for precise search

- **WHEN** a COORDINADOR calls `GET /api/encuentros/instancias?materia_id=M1&estado=realizado&fecha_desde=2026-03-01`
- **THEN** the response contains only "Realizado" instances for materia M1 from March 2026 onwards

### Requirement: ADMIN-VIEW-006 — Empty result returns 200 with empty list

The system SHALL return 200 with an empty JSON array `[]` when no instances match the
applied filters, regardless of the user's role.

#### Scenario: No matching instances returns empty list

- **WHEN** a COORDINADOR filters by a materia that has no instances
- **THEN** the system returns 200 with `[]`

### Requirement: ADMIN-VIEW-007 — Include slot title in response

The `InstanciaResponse` SHALL include `slot_id` and the slot's `titulo` (when the
instance belongs to a slot) so the admin view can display meaningful grouping.
Independent instances (without slot) SHALL return `null` for slot fields.

#### Scenario: Admin view includes slot title

- **WHEN** a COORDINADOR lists instances
- **THEN** each instance response includes `slot_id` and `slot_titulo` (the parent slot's title), or `null` if the instance has no slot

### Requirement: ADMIN-VIEW-008 — Ordered by fecha ascending

The system SHALL return instances ordered by `fecha` ascending when listing instances
for the admin view, to present a chronological timeline to COORDINADOR/ADMIN.

#### Scenario: Results are chronologically ordered

- **WHEN** a COORDINADOR lists instances with dates 2026-04-03, 2026-03-15, 2026-04-01
- **THEN** the response order is 2026-03-15, 2026-04-01, 2026-04-03
