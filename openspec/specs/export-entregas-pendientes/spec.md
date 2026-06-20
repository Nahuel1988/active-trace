## ADDED Requirements

### Requirement: Cross-reference completion report with grades to find uncorrected submissions
The system SHALL allow the user to upload a completion report from the LMS and cross-reference it with imported grades to identify submissions that are completed by the student but not yet graded (RN-07). This applies only to textual-scaled activities (RN-08).

#### Scenario: Identify textual activities with submission but no grade
- **WHEN** the user uploads a completion report for a subject×cohort
- **THEN** the system SHALL cross-reference it with existing `Calificacion` records
- **AND** return only activities with textual scale that have a submission marker but no grade

#### Scenario: Numeric activities excluded from pending list
- **WHEN** cross-referencing completion data
- **THEN** activities with numeric scale SHALL NOT be included in the pending list (RN-08)

#### Scenario: Export pending submissions as CSV
- **WHEN** calling `GET /api/analisis/entregas-pendientes/export` with the uploaded report reference
- **THEN** the response SHALL be a downloadable CSV with: student name, activity name, submission date, subject

#### Scenario: Empty pending list when all graded
- **WHEN** all textual activities have corresponding grades
- **THEN** the pending list SHALL be empty
- **AND** the response SHALL include a `todas_corregidas: true` flag
