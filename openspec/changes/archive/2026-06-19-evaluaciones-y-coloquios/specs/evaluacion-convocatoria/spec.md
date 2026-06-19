## ADDED Requirements

### Requirement: CRUD de convocatorias de evaluación (F7.3)

El sistema SHALL exponer endpoints CRUD para `Evaluacion` bajo `/api/coloquios`, protegidos por `require_permission("coloquios:gestionar")` (COORDINADOR, ADMIN). El modelo SHALL incluir: `materia_id` (FK → Materia), `cohorte_id` (FK → Cohorte), `tipo` (enum: Parcial | TP | Coloquio | Recuperatorio), `instancia` (denominación libre), `dias_disponibles` (entero — ventana en días según D2). El soft delete SHALL aplicarse: `DELETE` establece `deleted_at` y los listados excluyen registros borrados. Todas las consultas SHALL filtrar por `tenant_id` del JWT.

#### Scenario: Alta de convocatoria

- **WHEN** un COORDINADOR envía `POST /api/coloquios` con materia_id, cohorte_id, tipo=Coloquio, instancia="Coloquio Final", dias_disponibles=5
- **THEN** el sistema crea la Evaluacion, responde 201 con los datos creados y el `tenant_id` del JWT

#### Scenario: Alta rechazada sin permiso

- **WHEN** un ALUMNO envía `POST /api/coloquios`
- **THEN** el sistema responde 403 (fail-closed)

#### Scenario: Edición de convocatoria

- **WHEN** un COORDINADOR envía `PATCH /api/coloquios/{id}` modificando `dias_disponibles` de 5 a 10
- **THEN** el sistema actualiza el campo, responde 200 con los datos modificados

#### Scenario: Edición no afecta entidades de otro tenant

- **WHEN** un COORDINADOR del tenant A envía `PATCH /api/coloquios/{id}` de una convocatoria del tenant B
- **THEN** el sistema responde 404

#### Scenario: Borrado lógico de convocatoria

- **WHEN** un COORDINADOR envía `DELETE /api/coloquios/{id}`
- **THEN** el sistema establece `deleted_at`, responde 204 y la convocatoria deja de aparecer en listados

#### Scenario: Listado de convocatorias activas excluye borradas

- **WHEN** un COORDINADOR consulta `GET /api/coloquios`
- **THEN** el sistema retorna 200 con solo las convocatorias del tenant que no tienen `deleted_at` poblado

#### Scenario: Esquema rechaza campos extra

- **WHEN** un COORDINADOR envía `POST /api/coloquios` incluyendo un campo no declarado (ej. `color`)
- **THEN** el sistema responde 422 (Pydantic `extra='forbid'`)

### Requirement: Importación de candidatos habilitados a una convocatoria (F7.2)

El sistema SHALL exponer `POST /api/coloquios/{id}/candidatos`, protegido por `require_permission("coloquios:gestionar")`, que recibe `{ usuario_ids: UUID[] }` y asocia los ALUMNOs como candidatos habilitados para esa convocatoria. Según D3, los candidatos NO SHALL tener modelo separado: se verifican contra la tabla `usuario` (rol ALUMNO) y la pertenencia al mismo tenant. La operación SHALL ser idempotente: si un `usuario_id` ya está registrado, no se duplica.

#### Scenario: Importación exitosa de 3 candidatos

- **WHEN** un COORDINADOR envía `POST /api/coloquios/{id}/candidatos` con `usuario_ids = [u1, u2, u3]` todos ALUMNOs del mismo tenant
- **THEN** el sistema registra los 3 candidatos y responde 200 con `{ registrados: 3, rechazados: [] }`

#### Scenario: Candidato no perteneciente al tenant se rechaza

- **WHEN** un COORDINADOR envía `POST /api/coloquios/{id}/candidatos` incluyendo un `usuario_id` de otro tenant
- **THEN** el sistema rechaza ese usuario, responde con `{ registrados: N, rechazados: [{ usuario_id, motivo }] }`

#### Scenario: Candidato con rol no-ALUMNO se rechaza

- **WHEN** un COORDINADOR envía `POST /api/coloquios/{id}/candidatos` incluyendo un `usuario_id` con rol PROFESOR
- **THEN** el sistema rechaza ese usuario con motivo "El usuario no tiene rol ALUMNO"

#### Scenario: Idempotencia — mismo candidato no se duplica

- **WHEN** un COORDINADOR envía dos veces `POST /api/coloquios/{id}/candidatos` con el mismo `usuario_id`
- **THEN** la segunda ejecución reporta el usuario como ya registrado en `rechazados` sin duplicar

#### Scenario: Sin permiso se rechaza

- **WHEN** un ALUMNO envía `POST /api/coloquios/{id}/candidatos`
- **THEN** el sistema responde 403

### Requirement: Listado de convocatorias con métricas operativas (F7.4)

El sistema SHALL exponer `GET /api/coloquios`, protegido por `require_permission("coloquios:gestionar")`, que retorna todas las convocatorias activas del tenant con métricas derivadas: total de candidatos convocados, reservas activas y cupos libres (calculados como `dias_disponibles - reservas_activas`). Las métricas SHALL calcularse en tiempo real contra las tablas `reserva_evaluacion` y la lista de candidatos.

#### Scenario: Listado con métricas completa

- **WHEN** un COORDINADOR consulta `GET /api/coloquios`
- **THEN** cada convocatoria en la respuesta incluye `convocados`, `reservas_activas` y `cupos_libres` calculados en el momento

#### Scenario: Convocatoria sin candidatos muestra métricas en cero

- **WHEN** un COORDINADOR consulta `GET /api/coloquios` y existe una convocatoria sin candidatos importados
- **THEN** esa convocatoria muestra `convocados: 0`, `reservas_activas: 0`, `cupos_libres: <dias_disponibles>`

#### Scenario: Listado aislado por tenant

- **WHEN** un COORDINADOR del tenant A consulta `GET /api/coloquios`
- **THEN** el sistema retorna solo convocatorias del tenant A, sin ninguna del tenant B

### Requirement: Panel global de métricas de coloquios (F7.1)

El sistema SHALL exponer `GET /api/coloquios/metricas`, protegido por `require_permission("coloquios:gestionar")`, que retorna métricas agregadas de todo el tenant: total de alumnos cargados como candidatos (sin duplicados), cantidad de instancias activas, reservas activas totales y notas registradas. Estas métricas SHALL calcularse en tiempo real.

#### Scenario: Panel retorna métricas globales

- **WHEN** un ADMIN consulta `GET /api/coloquios/metricas`
- **THEN** el sistema responde 200 con `total_candidatos`, `instancias_activas`, `reservas_activas`, `notas_registradas`

#### Scenario: Sin convocatorias las métricas son cero

- **WHEN** un ADMIN consulta `GET /api/coloquios/metricas` sin ninguna convocatoria creada en el tenant
- **THEN** el sistema responde 200 con todos los contadores en 0

### Requirement: Agenda consolidada de reservas activas (F7.5)

El sistema SHALL exponer `GET /api/coloquios/agenda`, protegido por `require_permission("coloquios:gestionar")`, que retorna todas las reservas activas del tenant con datos de la convocatoria (materia, instancia) y del alumno (nombre, legajo). SHALL admitir filtros opcionales: `materia_id`, `cohorte_id`, `evaluacion_id`, rango de `fecha_hora`.

#### Scenario: Agenda completa sin filtros

- **WHEN** un COORDINADOR consulta `GET /api/coloquios/agenda`
- **THEN** el sistema retorna 200 con todas las reservas activas del tenant incluyendo materia, instancia, alumno y fecha_hora

#### Scenario: Agenda filtrada por materia

- **WHEN** un COORDINADOR consulta `GET /api/coloquios/agenda?materia_id=xxx`
- **THEN** el sistema retorna 200 solo con reservas de esa materia

#### Scenario: Agenda filtrada por rango de fechas

- **WHEN** un COORDINADOR consulta `GET /api/coloquios/agenda?fecha_desde=2026-07-01&fecha_hasta=2026-07-15`
- **THEN** el sistema retorna 200 solo con reservas dentro del rango

#### Scenario: Agenda solo incluye reservas Activas

- **WHEN** un COORDINADOR consulta `GET /api/coloquios/agenda`
- **THEN** las reservas con estado `Cancelada` no aparecen en la agenda
