## ADDED Requirements

### Requirement: CRUD de programas de materia con unicidad por combinación

El sistema SHALL gestionar programas de materia como documentos asociados a una combinación única `(materia_id × carrera_id × cohorte_id)` dentro del tenant.

#### Scenario: Crear programa con combinación nueva — happy path

- **GIVEN** un usuario con permiso `estructura:gestionar` en un tenant que tiene Materia M, Carrera C y Cohorte H
- **WHEN** el usuario invoca `POST /api/v1/programas` con `{materia_id: M, carrera_id: C, cohorte_id: H, titulo: "Programa 2026", referencia_archivo: "s3://bucket/prog.pdf"}`
- **THEN** el sistema responde 201 con el registro creado incluyendo `id`, `tenant_id`, `cargado_at`, `created_at`, `updated_at`

#### Scenario: Crear programa con combinación duplicada — 409

- **GIVEN** ya existe un `ProgramaMateria` activo para `(materia_id=M, carrera_id=C, cohorte_id=H)` en el tenant
- **WHEN** el usuario intenta crear otro para la misma combinación
- **THEN** el sistema responde 409

#### Scenario: Crear programa con materia inexistente — 404

- **WHEN** el usuario invoca `POST /api/v1/programas` con un `materia_id` que no existe en el tenant
- **THEN** el sistema responde 404 con detalle "materia not found"

#### Scenario: Crear programa con carrera inexistente — 404

- **WHEN** el usuario invoca `POST /api/v1/programas` con un `carrera_id` que no existe en el tenant
- **THEN** el sistema responde 404 con detalle "carrera not found"

#### Scenario: Crear programa con cohorte inexistente — 404

- **WHEN** el usuario invoca `POST /api/v1/programas` con un `cohorte_id` que no existe en el tenant
- **THEN** el sistema responde 404 con detalle "cohorte not found"

#### Scenario: Listar programas con filtros — solo del tenant

- **GIVEN** el tenant A tiene 2 programas y el tenant B tiene 1 programa
- **WHEN** un usuario del tenant A invoca `GET /api/v1/programas`
- **THEN** el sistema retorna solo los 2 programas del tenant A, nunca los del tenant B

#### Scenario: Listar programas con filtro por materia

- **GIVEN** el tenant tiene 3 programas para 2 materias distintas
- **WHEN** el usuario invoca `GET /api/v1/programas?materia_id={M}`
- **THEN** el sistema retorna solo los programas de la materia M

#### Scenario: Obtener programa por ID — 404 si no existe o es de otro tenant

- **WHEN** el usuario invoca `GET /api/v1/programas/{id}` con un ID inexistente o de otro tenant
- **THEN** el sistema responde 404

#### Scenario: Actualizar programa — solo titulo y referencia_archivo

- **GIVEN** existe un programa con `titulo="Original"`
- **WHEN** el usuario invoca `PUT /api/v1/programas/{id}` con `{titulo: "Actualizado"}`
- **THEN** el sistema responde 200 con el programa actualizado y `titulo="Actualizado"`

#### Scenario: Soft delete de programa

- **GIVEN** existe un programa activo
- **WHEN** el usuario invoca `DELETE /api/v1/programas/{id}`
- **THEN** el sistema responde 204 y el programa no aparece en listados posteriores (`deleted_at IS NOT NULL`)

#### Scenario: Soft delete de un ID inexistente — 404

- **WHEN** el usuario invoca `DELETE /api/v1/programas/{id}` con un ID que no existe
- **THEN** el sistema responde 404

#### Scenario: Acceso sin autenticación — 401

- **WHEN** se invoca cualquier endpoint de `/api/v1/programas` sin token JWT
- **THEN** el sistema responde 401

#### Scenario: Acceso sin permiso de gestión — 403

- **WHEN** se invoca `POST /api/v1/programas` con un usuario que no tiene `estructura:gestionar`
- **THEN** el sistema responde 403

#### Scenario: Campo extra en el body — 422

- **WHEN** se invoca `POST /api/v1/programas` con un campo no declarado en el schema (`extra='forbid'`)
- **THEN** el sistema responde 422

### Requirement: referencia_archivo es opcional y opaca

El sistema SHALL aceptar `POST /api/v1/programas` sin `referencia_archivo` (campo opcional). El valor, cuando está presente, SHALL almacenarse tal cual sin interpretarlo ni validar su formato.

#### Scenario: Crear programa sin referencia_archivo

- **WHEN** el usuario crea un programa sin enviar `referencia_archivo`
- **THEN** el registro se crea con `referencia_archivo = null` y el sistema responde 201
