## ADDED Requirements

### Requirement: Quick subject report with aggregated metrics
The system SHALL provide a quick report endpoint with key aggregated metrics for a given subject×cohort combination, based on imported grade data.

#### Scenario: Report includes total students, activities, and approval rate
- **WHEN** calling `GET /api/analisis/reportes` with `materia_id` and `cohorte_id`
- **THEN** the response SHALL include:
  - `total_alumnos`: total students in the cohort
  - `total_actividades`: distinct activities detected
  - `tasa_aprobacion_pct`: percentage of approved grades across all activities
  - `alumnos_atrasados`: count of atrasados students
  - `alumnos_al_dia`: count of on-track students

#### Scenario: Empty report when no data imported
- **WHEN** calling `GET /api/analisis/reportes` for a subject×cohort with no grade data
- **THEN** the system SHALL return zeros for all metrics and a `sin_datos: true` flag
