# Spec: encuentro-html-export

## Overview

Generation of an HTML block with the encounter schedule and recordings for embedding
in the LMS virtual classroom (F6.4, FL-06 step 7). The endpoint returns `text/html`
with a table of instances for a given slot, ordered chronologically. Each row includes
fecha, hora, título, estado, meet_url (if Programado), and video_url (if Realizado).
The PROFESOR copies this fragment manually and embeds it in the virtual classroom.

## ADDED Requirements

### Requirement: HTML-001 — Generate HTML block for a slot's instances

The system SHALL generate an HTML fragment (table or list) for the instances of a given slot.
The response Content-Type SHALL be `text/html`, not `application/json`.

#### Scenario: Successful HTML generation

- **WHEN** a user requests `GET /api/encuentros/slots/{slot_id}/html` for a valid slot with 3 instances
- **THEN** the system returns 200 with Content-Type `text/html` and a body containing an HTML `<table>` element

#### Scenario: HTML contains all instances ordered by date

- **WHEN** a user requests HTML for a slot with instances on dates 2026-03-09, 2026-03-02, 2026-03-16
- **THEN** the table rows appear in chronological order: 2026-03-02, 2026-03-09, 2026-03-16

### Requirement: HTML-002 — Include instance details in each row

Each row in the HTML table SHALL include: fecha, hora, título, estado, meet_url (if state
is Programado), and video_url (if state is Realizado). The meet_url SHALL be rendered as
a clickable link. The video_url SHALL be rendered as a clickable link. Empty/null fields
SHALL render as empty cells or be omitted.

#### Scenario: Programado instance row includes meet_url

- **WHEN** a Programado instance has `meet_url: "https://meet.example.com/session"` and `video_url: null`
- **THEN** the HTML row for that instance contains a clickable link for meet_url and no video_url link

#### Scenario: Realizado instance row includes video_url

- **WHEN** a Realizado instance has `video_url: "https://youtube.com/watch?v=abc"` and `meet_url: null`
- **THEN** the HTML row for that instance contains a clickable link for video_url and no meet_url link

### Requirement: HTML-003 — Scope by role for HTML export

The system SHALL enforce the same role-based access: PROFESOR/TUTOR can only generate
HTML for their own slots. COORDINADOR/ADMIN can generate HTML for any slot in the tenant.

#### Scenario: PROFESOR generates HTML for own slot

- **WHEN** a PROFESOR requests HTML for a slot they own
- **THEN** the system returns 200 with the HTML block

#### Scenario: PROFESOR cannot generate HTML for another user's slot

- **WHEN** a PROFESOR requests HTML for a slot belonging to a different user
- **THEN** the system returns 404

#### Scenario: COORDINADOR generates HTML for any slot

- **WHEN** a COORDINADOR requests HTML for any slot in the tenant
- **THEN** the system returns 200 with the HTML block

### Requirement: HTML-004 — Tenant isolation

The system SHALL isolate HTML export by tenant. A user from tenant A SHALL NOT access
HTML export for a slot in tenant B.

#### Scenario: Slot from tenant A produces 404 for tenant B user

- **WHEN** a user from tenant B requests HTML for a slot from tenant A
- **THEN** the system returns 404

### Requirement: HTML-005 — Edge cases for empty or invalid slots

The system SHALL handle edge cases: if the slot does not exist, return 404. If the slot
exists but has no instances (soft-deleted slot with instances from other slots, or
similarly unusual), return an HTML block with an empty table and header row only.

#### Scenario: Slot not found returns 404

- **WHEN** a user requests HTML for a non-existent `slot_id`
- **THEN** the system returns 404

#### Scenario: Slot with no instances returns empty HTML table

- **WHEN** a user requests HTML for a slot that exists but has 0 instances
- **THEN** the system returns 200 with an HTML table containing only the header row and no data rows
