## ADDED Requirements

### Requirement: Compute atrasados per subject×cohort
The system SHALL compute which students are "atrasados" (behind) for a given subject×cohort combination, based on their imported grades and the configured passing threshold.

#### Scenario: Student with missing activities is atrasado
- **WHEN** a student has activities marked as missing (no submission) for a subject×cohort
- **THEN** the student SHALL appear in the atrasados list for that subject×cohort

#### Scenario: Student with grade below threshold is atrasado
- **WHEN** a student has a numeric grade below the configured `umbral_pct` for that subject (RN-03)
- **THEN** the student SHALL appear in the atrasados list

#### Scenario: Student with textual non-passing grade is atrasado
- **WHEN** a student has a textual grade that is NOT in the configured `valores_aprobatorios` set
- **THEN** the student SHALL appear in the atrasados list

#### Scenario: Student with all passing grades is not atrasado
- **WHEN** a student has all activities completed with grades ≥ umbral (or passing textual values)
- **THEN** the student SHALL NOT appear in the atrasados list

#### Scenario: Atrasados list can be filtered
- **WHEN** calling `GET /api/analisis/atrasados` with `materia_id` and optionally `cohorte_id`
- **THEN** the system SHALL return only atrasados matching those filters
- **AND** the response SHALL include: student name+email, materia, missing vs below-threshold classification

#### Scenario: No umbral configured uses tenant default
- **WHEN** a subject has no `UmbralMateria` configured
- **THEN** the system SHALL use the tenant default threshold of 60%
