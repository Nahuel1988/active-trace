## ADDED Requirements

### Requirement: Panel de métricas globales de coloquios

El sistema SHALL mostrar un panel con 4 tarjetas de métricas obtenidas de `GET /api/v1/coloquios/metricas`: total candidatos, instancias activas, reservas activas, notas registradas.

#### Scenario: Coordinador ve panel de métricas
- **WHEN** un usuario con `coloquios:gestionar` navega a `/coloquios`
- **THEN** el sistema ejecuta `useQuery` con key `['coloquios', 'metricas']` y muestra 4 cards con valores

#### Scenario: Sin convocatorias muestra ceros
- **WHEN** no existen convocatorias en el tenant
- **THEN** todas las cards muestran 0

### Requirement: Listado de convocatorias con CRUD

El sistema SHALL mostrar un listado de convocatorias de coloquio (`GET /api/v1/coloquios`) con métricas inline (convocados, reservas activas, cupos libres). Permitir crear (`POST /api/v1/coloquios`) y soft-delete.

#### Scenario: Listado de convocatorias
- **WHEN** un usuario con `coloquios:gestionar` navega al listado
- **THEN** el sistema ejecuta `useQuery` y muestra tabla con métricas inline

#### Scenario: Crear convocatoria
- **WHEN** un usuario completa el formulario de nueva convocatoria
- **THEN** el sistema ejecuta `useMutation`, invalida `['coloquios']`, muestra toast

#### Scenario: Eliminar convocatoria
- **WHEN** un usuario confirma eliminación de una convocatoria
- **THEN** el sistema ejecuta `DELETE`, invalida `['coloquios']`

### Requirement: Agenda consolidada de reservas

El sistema SHALL mostrar una página de agenda consolidada (`GET /api/v1/coloquios/agenda`) con filtros por materia, cohorte, evaluación y rango de fechas. Muestra tabla con alumno, materia, fecha y hora.

#### Scenario: Ver agenda
- **WHEN** un usuario con `coloquios:gestionar` navega a `/coloquios/agenda`
- **THEN** el sistema ejecuta `useQuery` con key `['coloquios', 'agenda', filters]` y muestra tabla

#### Scenario: Filtrar agenda por materia
- **WHEN** el usuario selecciona una materia en el filtro
- **THEN** la query se refresca y muestra solo reservas de esa materia

### Requirement: Registro académico de coloquios

El sistema SHALL mostrar el registro académico (`GET /api/v1/coloquios/registro-academico`) con datos de notas registradas.

#### Scenario: Ver registro académico
- **WHEN** un usuario con `coloquios:gestionar` navega a `/coloquios/registro-academico`
- **THEN** el sistema ejecuta `useQuery` y muestra tabla de notas
