## ADDED Requirements

### Requirement: Fragmento LMS formateado con evaluaciones ordenadas

El sistema SHALL exponer un endpoint `GET /api/v1/fechas-academicas/lms-fragment` que devuelva un fragmento de texto formateado con todas las evaluaciones de una materia y cohorte, listo para publicar en el aula virtual del LMS. Las evaluaciones SHALL ordenarse por `fecha` ascendente.

El formato de cada línea SHALL ser: `- [Tipo #N] Titulo — DD/MM/YYYY`

#### Scenario: Fragmento con múltiples fechas — ordenado ascendente

- **GIVEN** el tenant tiene 3 fechas para `(materia_id=M, cohorte_id=H)`: 
  - `{tipo: "Coloquio", numero: 1, titulo: "Coloquio Final", fecha: 2026-06-20}`
  - `{tipo: "Parcial", numero: 1, titulo: "Primer Parcial", fecha: 2026-04-15}`
  - `{tipo: "TP", numero: 1, titulo: "TP Integrador", fecha: 2026-05-10}`
- **WHEN** el usuario invoca `GET /api/v1/fechas-academicas/lms-fragment?materia_id={M}&cohorte_id={H}`
- **THEN** el sistema responde 200 con:
```json
{"fragment": "- [Parcial #1] Primer Parcial — 15/04/2026\n- [TP #1] TP Integrador — 10/05/2026\n- [Coloquio #1] Coloquio Final — 20/06/2026"}
```

#### Scenario: Fragmento con una sola fecha

- **GIVEN** el tenant tiene una sola fecha para la combinación
- **WHEN** el usuario invoca `GET /api/v1/fechas-academicas/lms-fragment?materia_id={M}&cohorte_id={H}`
- **THEN** el sistema responde 200 con el fragmento conteniendo una sola línea

#### Scenario: Fragmento con fechas del mismo tipo y distinto numero

- **GIVEN** el tenant tiene `Parcial #1` y `Parcial #2` para la misma materia y cohorte
- **WHEN** el usuario invoca el endpoint
- **THEN** el fragmento incluye ambas líneas con `[Parcial #1]` y `[Parcial #2]`

### Requirement: Fragmento vacío cuando no hay evaluaciones

El sistema SHALL retornar el texto `"Sin evaluaciones registradas"` en el campo `fragment` cuando no existan fechas académicas para la combinación `(materia_id, cohorte_id)` solicitada.

#### Scenario: Sin evaluaciones registradas

- **GIVEN** no existen fechas académicas para `(materia_id=M, cohorte_id=H)`
- **WHEN** el usuario invoca `GET /api/v1/fechas-academicas/lms-fragment?materia_id={M}&cohorte_id={H}`
- **THEN** el sistema responde 200 con `{"fragment": "Sin evaluaciones registradas"}`

### Requirement: Parámetros materia_id y cohorte_id obligatorios

El sistema SHALL requerir los parámetros `materia_id` y `cohorte_id` como query params obligatorios en `GET /api/v1/fechas-academicas/lms-fragment`. Si alguno falta, el sistema SHALL responder 422.

#### Scenario: Falta materia_id — 422

- **WHEN** el usuario invoca `GET /api/v1/fechas-academicas/lms-fragment?cohorte_id={H}` sin `materia_id`
- **THEN** el sistema responde 422

#### Scenario: Falta cohorte_id — 422

- **WHEN** el usuario invoca `GET /api/v1/fechas-academicas/lms-fragment?materia_id={M}` sin `cohorte_id`
- **THEN** el sistema responde 422

#### Scenario: Faltan ambos parámetros — 422

- **WHEN** el usuario invoca `GET /api/v1/fechas-academicas/lms-fragment` sin parámetros
- **THEN** el sistema responde 422

### Requirement: build_lms_fragment como función pura

El sistema SHALL implementar `build_lms_fragment(fechas: list[FechaAcademica]) -> str` como una función pura sin efectos secundarios ni I/O. Dada la misma lista de fechas, SHALL producir siempre el mismo fragmento. La función NO SHALL acceder a la base de datos ni depender del estado del sistema.

#### Scenario: Misma entrada produce mismo resultado

- **GIVEN** una lista de 2 fechas académicas
- **WHEN** se invoca `build_lms_fragment` dos veces con la misma lista
- **THEN** ambos resultados son idénticos

#### Scenario: Función no realiza operaciones de I/O

- **WHEN** se invoca `build_lms_fragment` con una lista vacía
- **THEN** retorna `"Sin evaluaciones registradas"` sin realizar consultas a la base de datos

### Requirement: Aislamiento multi-tenant en LMS fragment

El endpoint `/lms-fragment` SHALL respetar el aislamiento multi-tenant: solo SHALL devolver fechas del tenant del usuario autenticado.

#### Scenario: Fragmento solo incluye fechas del tenant actual

- **GIVEN** el tenant A tiene fechas para `(materia=M, cohorte=H)` y el tenant B tiene fechas para la misma combinación aparente
- **WHEN** un usuario del tenant A invoca `GET /api/v1/fechas-academicas/lms-fragment?materia_id={M}&cohorte_id={H}`
- **THEN** el fragmento incluye solo las fechas del tenant A, nunca las del tenant B

### Requirement: Control de acceso en LMS fragment

El endpoint `/lms-fragment` SHALL requerir el permiso `estructura:ver` para su acceso. Sin autenticación SHALL responder 401. Sin permiso SHALL responder 403.

#### Scenario: LMS fragment sin autenticación — 401

- **WHEN** se invoca `GET /api/v1/fechas-academicas/lms-fragment?materia_id={M}&cohorte_id={H}` sin token JWT
- **THEN** el sistema responde 401

#### Scenario: LMS fragment sin permiso de lectura — 403

- **WHEN** se invoca el endpoint con un usuario que no tiene `estructura:ver`
- **THEN** el sistema responde 403
