## ADDED Requirements

### Requirement: Ranking of approved activities per subject
The system SHALL compute a descending ranking of students by count of approved activities per subject×cohort (RN-09). Only students with at least one approved activity SHALL be included.

#### Scenario: Ranking ordered by approved count descending
- **WHEN** calling `GET /api/analisis/ranking` with `materia_id` and `cohorte_id`
- **THEN** the system SHALL return students ordered by approved activities count descending
- **AND** each entry SHALL include: student name, approved count, total activities, approval percentage

#### Scenario: Students without any approved activity excluded
- **WHEN** a student has zero approved activities in the subject
- **THEN** that student SHALL NOT appear in the ranking response

#### Scenario: Tie-breaking by alphabetical order
- **WHEN** two or more students have the same approved count
- **THEN** they SHALL be ordered alphabetically by last name, then first name
