## ADDED Requirements

### Requirement: General student activity monitor (coordination/admin)
The system SHALL provide a cross-subject view of all students' activity status across the tenant (F2.7), accessible to COORDINADOR and ADMIN.

#### Scenario: General monitor shows all students with filters
- **WHEN** calling `GET /api/monitores/general` with optional filters (`materia_id`, `regional`, `comision`, `q` free text)
- **THEN** the response SHALL return a paginated list of students with: name, email, subject, commission, approved count, pending count, atrasado status
- **AND** the endpoint SHALL support export with `format=csv`

#### Scenario: General monitor filter by activity state
- **WHEN** calling with `estado=atrasado`
- **THEN** only students classified as atrasados SHALL be returned

### Requirement: Tutor/professor student tracking monitor
The system SHALL provide a filtered view of activity status limited to students assigned to the current user (F2.8), accessible to TUTOR and PROFESOR.

#### Scenario: Tutor monitor scoped to own students
- **WHEN** a TUTOR or PROFESOR calls `GET /api/monitores/seguimiento`
- **THEN** the response SHALL only include students from their own subject×cohort assignments
- **AND** SHALL support the same filters as the general monitor minus `regional`

#### Scenario: Coordination monitor adds date range filter
- **WHEN** a COORDINADOR or ADMIN calls `GET /api/monitores/seguimiento` with `fecha_desde` and `fecha_hasta`
- **THEN** the response SHALL be scoped to the given date range (F2.9)
