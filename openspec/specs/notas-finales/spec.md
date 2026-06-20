## ADDED Requirements

### Requirement: Final grades grouped by student
The system SHALL compute final grades per student for a given subject×cohort, aggregating all imported activity grades.

#### Scenario: Final grades grouped per student
- **WHEN** calling `GET /api/analisis/notas-finales` with `materia_id` and `cohorte_id`
- **THEN** the response SHALL return a list of students, each with:
  - Student name, email
  - Per-activity breakdown: activity name, numeric or textual grade, approved boolean
  - Final computed grade (average of numeric grades, or textual summary)

#### Scenario: Only numeric activities averaged for final grade
- **WHEN** computing the final numeric grade
- **THEN** only activities with `nota_numerica` SHALL be averaged
- **AND** activities with only `nota_textual` SHALL be listed separately without affecting the numeric average

#### Scenario: Exportable response format
- **WHEN** calling `GET /api/analisis/notas-finales` with `format=csv`
- **THEN** the response SHALL be a downloadable CSV file with the same data structure
