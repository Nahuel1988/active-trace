## ADDED Requirements

### Requirement: Registro de nota final por alumno por convocatoria (D4)

El sistema SHALL exponer `POST /api/coloquios/{id}/resultados`, protegido por `require_permission("coloquios:gestionar")` (COORDINADOR, ADMIN), que registra la `nota_final` de un ALUMNO en una convocatoria. El body SHALL incluir `alumno_id` y `nota_final` (texto — admite valores numéricos como "8" o cualitativos como "Aprobado" según D4). El resultado SHALL existir independientemente de si el ALUMNO tiene o no una `ReservaEvaluacion` (D4). La unicidad SHALL ser `(tenant_id, evaluacion_id, alumno_id)` — no puede haber dos resultados para el mismo alumno en la misma convocatoria. El sistema SHALL verificar que `alumno_id` pertenezca al mismo tenant y que la convocatoria exista y esté activa (no soft-deleted).

#### Scenario: Registro de nota para alumno con reserva

- **WHEN** un COORDINADOR envía `POST /api/coloquios/{id}/resultados` con `alumno_id` de un ALUMNO candidato y `nota_final = "8"`
- **THEN** el sistema crea el ResultadoEvaluacion y responde 201

#### Scenario: Registro de nota para alumno sin reserva (D4)

- **WHEN** un COORDINADOR envía `POST /api/coloquios/{id}/resultados` con `alumno_id` de un ALUMNO candidato que NO tiene reserva en la convocatoria
- **THEN** el sistema crea el resultado igualmente y responde 201

#### Scenario: Nota cualitativa se acepta

- **WHEN** un COORDINADOR envía `POST /api/coloquios/{id}/resultados` con `nota_final = "Aprobado"`
- **THEN** el sistema acepta el valor textual y responde 201

#### Scenario: Duplicado de resultado se rechaza

- **WHEN** un COORDINADOR envía `POST /api/coloquios/{id}/resultados` dos veces para el mismo `(evaluacion_id, alumno_id)`
- **THEN** el sistema responde 409 y el segundo registro no se crea

#### Scenario: Resultado para alumno de otro tenant se rechaza

- **WHEN** un COORDINADOR envía `POST /api/coloquios/{id}/resultados` con `alumno_id` de un usuario de otro tenant
- **THEN** el sistema responde 404 (fail-closed por tenant)

#### Scenario: Sin permiso se rechaza

- **WHEN** un ALUMNO envía `POST /api/coloquios/{id}/resultados`
- **THEN** el sistema responde 403

### Requirement: Actualización de nota final

El sistema SHALL exponer `PATCH /api/coloquios/{id}/resultados/{resultado_id}`, protegido por `require_permission("coloquios:gestionar")`, que permite modificar `nota_final` de un resultado existente. SHALL registrar el cambio en el AuditLog con código `COLOQUIO_MODIFICAR_RESULTADO`.

#### Scenario: Actualización exitosa de nota

- **WHEN** un COORDINADOR envía `PATCH /api/coloquios/{id}/resultados/{resultado_id}` con `nota_final = "9"`
- **THEN** el sistema actualiza la nota, responde 200 y emite evento de auditoría `COLOQUIO_MODIFICAR_RESULTADO`

#### Scenario: Actualización de resultado de otro tenant se rechaza

- **WHEN** un COORDINADOR del tenant A envía `PATCH /api/coloquios/{id}/resultados/{resultado_id}` de un resultado del tenant B
- **THEN** el sistema responde 404

### Requirement: Consulta de resultados por convocatoria

El sistema SHALL exponer `GET /api/coloquios/{id}/resultados`, protegido por `require_permission("coloquios:gestionar")`, que retorna todos los resultados registrados en una convocatoria, incluyendo datos del alumno (nombre, legajo) y la nota. SHALL filtrar por `tenant_id` del JWT.

#### Scenario: Listado de resultados de una convocatoria

- **WHEN** un COORDINADOR consulta `GET /api/coloquios/{id}/resultados`
- **THEN** el sistema retorna 200 con todos los resultados de esa convocatoria del tenant, con datos del alumno y nota

#### Scenario: Consulta de convocatoria de otro tenant retorna 404

- **WHEN** un COORDINADOR del tenant A consulta `GET /api/coloquios/{id}/resultados` de una convocatoria del tenant B
- **THEN** el sistema responde 404

### Requirement: Registro académico consolidado de coloquios

El sistema SHALL exponer `GET /api/coloquios/registro-academico`, protegido por `require_permission("coloquios:gestionar")`, que retorna todos los resultados de coloquios del tenant consolidados, incluyendo materia, instancia, fecha de la convocatoria, datos del alumno y nota. SHALL admitir filtros opcionales: `materia_id`, `cohorte_id`, `alumno_id`. Los ALUMNOs SHALL poder consultar su propio registro académico vía `GET /api/coloquios/mi-registro` (protegido por `coloquios:reservar`), viendo únicamente sus propios resultados.

#### Scenario: COORDINADOR consulta registro académico consolidado

- **WHEN** un COORDINADOR consulta `GET /api/coloquios/registro-academico`
- **THEN** el sistema retorna 200 con todos los resultados del tenant, incluyendo materia, instancia, alumno y nota

#### Scenario: Registro filtrado por materia

- **WHEN** un COORDINADOR consulta `GET /api/coloquios/registro-academico?materia_id=xxx`
- **THEN** el sistema retorna 200 solo con resultados de esa materia

#### Scenario: ALUMNO consulta su propio registro

- **WHEN** un ALUMNO consulta `GET /api/coloquios/mi-registro`
- **THEN** el sistema retorna 200 solo con sus propios resultados (identidad desde JWT)

#### Scenario: ALUMNO no ve resultados de otros alumnos

- **WHEN** un ALUMNO consulta `GET /api/coloquios/mi-registro`
- **THEN** el sistema no incluye resultados de otros ALUMNOs, aunque pertenezcan al mismo tenant

#### Scenario: Aislamiento por tenant en registro académico

- **WHEN** un COORDINADOR consulta `GET /api/coloquios/registro-academico`
- **THEN** el sistema retorna solo resultados del tenant del JWT
