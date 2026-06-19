## ADDED Requirements

### Requirement: CRUD de fechas académicas con unicidad por combinación

El sistema SHALL gestionar fechas académicas (instancias evaluativas) asociadas a una combinación única `(tenant_id, materia_id, cohorte_id, tipo, numero)` dentro del tenant. El campo `tipo` SHALL ser un enum con valores: `Parcial`, `TP`, `Coloquio`, `Recuperatorio`. El campo `numero` SHALL ser un entero ≥ 1. El sistema SHALL rechazar duplicados con 409.

#### Scenario: Crear fecha académica con combinación nueva — happy path

- **GIVEN** un usuario con permiso `estructura:gestionar` en un tenant que tiene Materia M y Cohorte H
- **WHEN** el usuario invoca `POST /api/v1/fechas-academicas` con `{materia_id: M, cohorte_id: H, tipo: "Parcial", numero: 1, periodo: "2026-1", fecha: "2026-04-15T14:00:00Z", titulo: "Primer Parcial"}`
- **THEN** el sistema responde 201 con el registro creado incluyendo `id`, `tenant_id`, `created_at`, `updated_at`

#### Scenario: Crear fecha con combinación duplicada — 409

- **GIVEN** ya existe una `FechaAcademica` activa para `(materia_id=M, cohorte_id=H, tipo="Parcial", numero=1)` en el tenant
- **WHEN** el usuario intenta crear otra con la misma combinación
- **THEN** el sistema responde 409

#### Scenario: Crear fecha con mismo tipo pero distinto numero — 201

- **GIVEN** ya existe una `FechaAcademica` activa para `(materia_id=M, cohorte_id=H, tipo="Parcial", numero=1)`
- **WHEN** el usuario crea una con `tipo="Parcial", numero=2` para la misma materia y cohorte
- **THEN** el sistema responde 201

#### Scenario: Crear fecha con tipo fuera del enum — 422

- **WHEN** el usuario invoca `POST /api/v1/fechas-academicas` con `tipo: "ExamenFinal"` (valor no válido)
- **THEN** el sistema responde 422

#### Scenario: Crear fecha con numero cero — 422

- **WHEN** el usuario invoca `POST /api/v1/fechas-academicas` con `numero: 0`
- **THEN** el sistema responde 422

#### Scenario: Crear fecha con numero negativo — 422

- **WHEN** el usuario invoca `POST /api/v1/fechas-academicas` con `numero: -1`
- **THEN** el sistema responde 422

#### Scenario: Todos los valores del enum tipo son aceptados

- **WHEN** el usuario crea fechas con cada valor del enum: `"Parcial"`, `"TP"`, `"Coloquio"`, `"Recuperatorio"`
- **THEN** el sistema responde 201 en cada caso

### Requirement: Validación de entidades referenciadas antes del INSERT

El sistema SHALL validar que `materia_id` y `cohorte_id` existan y pertenezcan al mismo tenant antes de insertar una fecha académica. Si cualquiera no existe, el sistema SHALL responder 404 con el detalle de qué entidad falta.

#### Scenario: Crear fecha con materia inexistente — 404

- **WHEN** el usuario invoca `POST /api/v1/fechas-academicas` con un `materia_id` que no existe en el tenant
- **THEN** el sistema responde 404 con detalle "materia not found"

#### Scenario: Crear fecha con cohorte inexistente — 404

- **WHEN** el usuario invoca `POST /api/v1/fechas-academicas` con un `cohorte_id` que no existe en el tenant
- **THEN** el sistema responde 404 con detalle "cohorte not found"

### Requirement: Aislamiento multi-tenant en fechas académicas

El sistema SHALL aislar las fechas académicas por tenant. Un usuario de un tenant SHALL poder ver y gestionar solo las fechas de su propio tenant.

#### Scenario: Listar fechas — solo del tenant

- **GIVEN** el tenant A tiene 3 fechas y el tenant B tiene 2 fechas
- **WHEN** un usuario del tenant A invoca `GET /api/v1/fechas-academicas`
- **THEN** el sistema retorna solo las 3 fechas del tenant A, nunca las del tenant B

#### Scenario: Obtener fecha por ID — 404 si es de otro tenant

- **GIVEN** existe una fecha con ID `F1` en el tenant B
- **WHEN** un usuario del tenant A invoca `GET /api/v1/fechas-academicas/{F1}`
- **THEN** el sistema responde 404

### Requirement: Listado con filtros por materia, cohorte, periodo y tipo

El sistema SHALL permitir filtrar el listado de fechas académicas por los parámetros opcionales `materia_id`, `cohorte_id`, `periodo` y `tipo`. Sin filtros, SHALL retornar todas las fechas activas del tenant.

#### Scenario: Filtrar por materia

- **GIVEN** el tenant tiene fechas para 2 materias distintas
- **WHEN** el usuario invoca `GET /api/v1/fechas-academicas?materia_id={M}`
- **THEN** el sistema retorna solo las fechas de la materia M

#### Scenario: Filtrar por periodo exacto

- **GIVEN** el tenant tiene fechas en los periodos "2026-1" y "2026-2"
- **WHEN** el usuario invoca `GET /api/v1/fechas-academicas?periodo=2026-1`
- **THEN** el sistema retorna solo las fechas del periodo "2026-1"

#### Scenario: Filtrar por tipo

- **GIVEN** el tenant tiene fechas de tipo "Parcial" y "TP"
- **WHEN** el usuario invoca `GET /api/v1/fechas-academicas?tipo=Parcial`
- **THEN** el sistema retorna solo las fechas de tipo "Parcial"

#### Scenario: Combinar múltiples filtros

- **WHEN** el usuario invoca `GET /api/v1/fechas-academicas?materia_id={M}&cohorte_id={H}&periodo=2026-1&tipo=Parcial`
- **THEN** el sistema retorna solo las fechas que cumplen todas las condiciones simultáneamente

### Requirement: Listado ordenado por fecha ascendente

El sistema SHALL retornar las fechas académicas ordenadas por `fecha` ascendente (más próxima primero).

#### Scenario: Orden por defecto ascendente

- **GIVEN** el tenant tiene fechas con fechas 2026-05-01, 2026-03-15 y 2026-07-20
- **WHEN** el usuario invoca `GET /api/v1/fechas-academicas`
- **THEN** el sistema retorna las fechas en orden: 2026-03-15, 2026-05-01, 2026-07-20

### Requirement: Actualización parcial de fecha académica

El sistema SHALL permitir actualizar solo los campos `periodo`, `fecha` y `titulo` de una fecha académica existente. Los campos `materia_id`, `cohorte_id`, `tipo` y `numero` NO SHALL ser modificables después de la creación.

#### Scenario: Actualizar titulo de fecha — 200

- **GIVEN** existe una fecha con `titulo="Original"`
- **WHEN** el usuario invoca `PUT /api/v1/fechas-academicas/{id}` con `{titulo: "Actualizado"}`
- **THEN** el sistema responde 200 con el registro actualizado y `titulo="Actualizado"`

#### Scenario: Actualizar fecha y periodo — 200

- **WHEN** el usuario invoca `PUT /api/v1/fechas-academicas/{id}` con `{fecha: "2026-06-01T10:00:00Z", periodo: "2026-2"}`
- **THEN** el sistema responde 200 con ambos campos actualizados

#### Scenario: Actualizar fecha inexistente — 404

- **WHEN** el usuario invoca `PUT /api/v1/fechas-academicas/{id}` con un ID que no existe
- **THEN** el sistema responde 404

### Requirement: Soft delete de fecha académica

El sistema SHALL soportar soft-delete de fechas académicas. Una fecha eliminada SHALL tener `deleted_at` con timestamp y NO SHALL aparecer en listados ni vistas posteriores.

#### Scenario: Soft delete exitoso — 204

- **GIVEN** existe una fecha activa
- **WHEN** el usuario invoca `DELETE /api/v1/fechas-academicas/{id}`
- **THEN** el sistema responde 204 y la fecha no aparece en listados posteriores

#### Scenario: Soft delete de ID inexistente — 404

- **WHEN** el usuario invoca `DELETE /api/v1/fechas-academicas/{id}` con un ID que no existe
- **THEN** el sistema responde 404

### Requirement: Vista calendario agrupada por período

El sistema SHALL exponer un endpoint `GET /api/v1/fechas-academicas/calendario` que agrupa las fechas activas por período. Cada grupo SHALL contener `periodo` y `fechas` (array de fechas ordenadas ascendentemente). Los grupos SHALL ordenarse alfabéticamente por período.

#### Scenario: Calendario agrupa por periodo correctamente

- **GIVEN** el tenant tiene fechas en periodos "2026-2" (3 fechas) y "2026-1" (2 fechas)
- **WHEN** el usuario invoca `GET /api/v1/fechas-academicas/calendario?materia_id={M}&cohorte_id={H}`
- **THEN** el sistema retorna un array con 2 grupos, ordenados alfabéticamente: primero "2026-1" con 2 fechas, luego "2026-2" con 3 fechas

#### Scenario: Calendario con filtro por materia

- **WHEN** el usuario invoca `GET /api/v1/fechas-academicas/calendario?materia_id={M}`
- **THEN** el sistema retorna solo las fechas de la materia M, agrupadas por período

### Requirement: Control de acceso en fechas académicas

El sistema SHALL requerir el permiso `estructura:gestionar` para operaciones de escritura (POST, PUT, DELETE) y `estructura:ver` para operaciones de lectura (GET). Sin autenticación SHALL responder 401. Sin permiso SHALL responder 403.

#### Scenario: Acceso sin autenticación — 401

- **WHEN** se invoca cualquier endpoint de `/api/v1/fechas-academicas` sin token JWT
- **THEN** el sistema responde 401

#### Scenario: Crear sin permiso de gestión — 403

- **WHEN** se invoca `POST /api/v1/fechas-academicas` con un usuario que no tiene `estructura:gestionar`
- **THEN** el sistema responde 403

#### Scenario: Listar sin permiso de lectura — 403

- **WHEN** se invoca `GET /api/v1/fechas-academicas` con un usuario que no tiene `estructura:ver`
- **THEN** el sistema responde 403

#### Scenario: Calendario sin autenticación — 401

- **WHEN** se invoca `GET /api/v1/fechas-academicas/calendario` sin token JWT
- **THEN** el sistema responde 401

### Requirement: Campo extra rechazado en schemas

El sistema SHALL rechazar con 422 cualquier request body que contenga campos no declarados en el schema Pydantic (`extra='forbid'`).

#### Scenario: Campo extra en creación — 422

- **WHEN** se invoca `POST /api/v1/fechas-academicas` con un campo no declarado como `"extra": "valor"`
- **THEN** el sistema responde 422
