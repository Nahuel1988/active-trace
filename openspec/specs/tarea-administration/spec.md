## Requirements

### Requirement: Vista "mis tareas"
El sistema SHALL exponer `GET /api/tareas/mias` que retorna las tareas donde el usuario autenticado es `asignado_a`. El criterio SHALL derivarse de la sesión (JWT), nunca de un parámetro de la petición.

#### Scenario: Docente ve solo sus tareas asignadas
- **WHEN** un PROFESOR solicita `GET /api/tareas/mias`
- **THEN** el sistema retorna 200 con las tareas donde ese usuario es `asignado_a`, y ninguna asignada a otros

#### Scenario: "Mis tareas" no incluye tareas de otro tenant
- **WHEN** un PROFESOR del tenant A solicita `GET /api/tareas/mias`
- **THEN** el sistema retorna solo tareas del tenant A

### Requirement: Administración global de tareas con filtros
El sistema SHALL exponer `GET /api/tareas` con filtros opcionales por `asignado_a`, `asignado_por`, `materia_id`, `estado` y `q` (búsqueda libre sobre la descripción). Los filtros SHALL combinarse en conjunción y aplicarse siempre dentro del tenant del usuario.

#### Scenario: Filtrar por docente asignado y estado
- **WHEN** un COORDINADOR solicita `GET /api/tareas?asignado_a={uid}&estado=EnProgreso`
- **THEN** el sistema retorna solo las tareas del tenant asignadas a ese usuario en estado `EnProgreso`

#### Scenario: Búsqueda libre por descripción
- **WHEN** un COORDINADOR solicita `GET /api/tareas?q=padron`
- **THEN** el sistema retorna las tareas del tenant cuya `descripcion` contiene el término (case-insensitive)

#### Scenario: Sin filtros retorna todas las tareas del tenant
- **WHEN** un ADMIN solicita `GET /api/tareas` sin filtros
- **THEN** el sistema retorna todas las tareas no borradas del tenant

### Requirement: Alcance de la administración según rol
El sistema SHALL limitar el listado global según el rol efectivo de la sesión. Un PROFESOR SHALL ver únicamente tareas donde es `asignado_a` o `asignado_por`. Un COORDINADOR o ADMIN SHALL ver todas las tareas del tenant.

#### Scenario: PROFESOR ve solo tareas en las que participa
- **WHEN** un PROFESOR solicita `GET /api/tareas`
- **THEN** el sistema retorna solo tareas donde es `asignado_a` o `asignado_por`, aun sin filtros explícitos

#### Scenario: COORDINADOR ve todas las tareas del tenant
- **WHEN** un COORDINADOR solicita `GET /api/tareas`
- **THEN** el sistema retorna todas las tareas no borradas del tenant
